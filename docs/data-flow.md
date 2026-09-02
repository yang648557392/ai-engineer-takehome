# Vantel QA data flow and contracts

This document shows the concrete values passed between pipeline stages. It is
intended to make the type annotations and nested SDK responses easier to read.

## End-to-end map

~~~text
data files
  -> loader.py       -> list[SourceDocument]
  -> chunker.py      -> list[DocumentChunk]
  -> openrouter.py   -> list[list[float]]
  -> indexer.py      -> Chroma collection

question: str
  -> openrouter.py   -> one query vector
  -> retriever.py    -> list[RetrievedChunk]
  -> answerer.py     -> context: str
  -> chat model      -> answer: str

evals/cases.yaml
  -> evaluation.py  -> list[EvalCase]
  -> answerer.py     -> answer plus retrieved chunks
  -> score_case      -> CaseResult
  -> SQLite          -> evaluation_runs and evaluation_results
~~~

## 1. Source files to SourceDocument

<code>loader.load_document(path)</code> reads one Markdown, CSV, or email file
and returns one complete source object:

~~~python
SourceDocument(
    doc_id="D003",
    title="Kettlebridge finance memo",
    source_type="markdown",
    content="The source body without YAML frontmatter...",
    path=Path("data/D003-kettlebridge-finance-memo.md"),
    date="2027-07-15",
)
~~~

The source-level <code>doc_id</code> is shown in answer citations. It comes from
Markdown frontmatter when available and otherwise from a <code>Dxxx</code>
token in the filename.

<code>loader.load_documents(data_dir)</code> returns
<code>list[SourceDocument]</code>. The current corpus contains 32 objects.

## 2. SourceDocument to DocumentChunk

<code>chunker.chunk_documents(documents)</code> converts complete files to
retrieval units:

~~~python
DocumentChunk(
    chunk_id="D003-000",
    doc_id="D003",
    title="Kettlebridge finance memo",
    source_type="markdown",
    content="Text for this retrieval unit...",
    path=Path("data/D003-kettlebridge-finance-memo.md"),
    position=0,
    date="2027-07-15",
    section=None,
)
~~~

The identifiers serve different purposes:

- <code>doc_id</code> identifies the source displayed as <code>[D003]</code>.
- <code>chunk_id</code> identifies one Chroma record used by
  <code>upsert</code>.

The current 32 source documents produce 38 chunks.

### Format-specific behavior

- Small Markdown and CSV files normally remain one chunk.
- Email threads are separated into messages before size-based splitting.
- Text over 2,400 characters is split near paragraph boundaries.
- Adjacent oversized pieces overlap by 250 characters.
- Chunk positions start at zero within each source document.

## 3. Embedding input and output

<code>DocumentChunk.embedding_text</code> adds identity context:

~~~text
Document ID: D003
Title: Kettlebridge finance memo
Date: 2027-07-15
Section: ARR restatement
Text for this retrieval unit...
~~~

<code>openrouter.embed_texts</code> accepts <code>list[str]</code> and returns
<code>list[list[float]]</code>.

The outer list contains one vector per input string. The inner list contains
the numbers in that vector:

~~~text
38 chunk texts -> shape 38 x 1536
1 question     -> shape  1 x 1536
~~~

The provider response includes the original input index for each vector. The
adapter sorts by that index so vector N stays aligned with text N.

## 4. Chroma record layout

<code>indexer.index_chunks</code> passes four parallel lists to Chroma:

~~~python
collection.upsert(
    ids=[chunk.chunk_id for chunk in chunks],
    embeddings=vectors,
    documents=[chunk.content for chunk in chunks],
    metadatas=[chunk.metadata for chunk in chunks],
)
~~~

At position N, all four values describe the same chunk:

~~~text
ids[N]         -> D003-000
embeddings[N]  -> the 1,536 floats for D003-000
documents[N]   -> the text for D003-000
metadatas[N]   -> source fields for D003-000
~~~

One metadata mapping looks like:

~~~python
{
    "doc_id": "D003",
    "title": "Kettlebridge finance memo",
    "source_type": "markdown",
    "path": "data/D003-kettlebridge-finance-memo.md",
    "position": 0,
    "date": "2027-07-15",
}
~~~

The chunk ID is passed separately through the Chroma <code>ids</code> field.
Optional <code>date</code> and <code>section</code> keys are omitted when
absent because Chroma metadata values must be scalar.

## 5. Chroma query result shape

Chroma accepts a batch of query vectors. It therefore returns an outer list per
query and an inner list per match:

~~~python
{
    "ids": [
        ["D003-000", "D002-000"]
    ],
    "documents": [
        ["Restated ARR text...", "Original board deck text..."]
    ],
    "metadatas": [
        [
            {"doc_id": "D003", "title": "Finance memo", "position": 0},
            {"doc_id": "D002", "title": "Board deck", "position": 0},
        ]
    ],
    "distances": [
        [0.10, 0.18]
    ],
}
~~~

The general shape is:

~~~text
result[field][query_number][match_number]
~~~

This project sends one question per call. Therefore
<code>result["documents"][0]</code> means "all document matches for the first
and only question." It does not mean "the first matched document."

The retriever zips the parallel fields and converts each match to:

~~~python
RetrievedChunk(
    chunk_id="D003-000",
    doc_id="D003",
    title="Finance memo",
    content="Restated ARR text...",
    score=0.90,
    position=0,
    date="2027-07-15",
    section=None,
)
~~~

The score is <code>1.0 - cosine_distance</code>, so a larger value represents
a closer match.

## 6. Answer-generation contract

<code>answerer.build_context</code> converts retrieved objects into one prompt
string:

~~~text
SOURCE [D003] — Finance memo — 2027-07-15
Restated ARR text...

SOURCE [D002] — Board deck — 2027-06-30
Original ARR text...
~~~

The chat request contains:

~~~python
[
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": "Question:\n...\n\nRetrieved sources:\n...",
    },
]
~~~

The provider can return multiple candidate choices. This project requests one
and reads:

~~~python
response.choices[0].message.content
~~~

<code>answer_question</code> returns both output and evidence:

~~~python
tuple[str, list[RetrievedChunk]]
#     answer       retrieved evidence
~~~

Every cited source ID must be among the retrieved documents. This prevents
invented IDs but does not prove that the cited text supports the exact claim.

## 7. Evaluation YAML to typed cases

<code>yaml.safe_load</code> initially produces ordinary nested containers:

~~~python
{
    "cases": [
        {
            "id": "q01",
            "question": "What was ...?",
            "answerable": True,
            "expected_answer": "...",
            "required_patterns": ["...", "..."],
            "expected_citations": ["D002", "D003"],
            "relevant_documents": ["D002", "D003"],
        }
    ]
}
~~~

The evaluator checks the outer dictionary and list, then converts every case
dictionary to an <code>EvalCase</code>. Later code can use named attributes
such as <code>case.question</code> instead of nested dictionary keys.

Each case follows:

~~~text
EvalCase
  -> answer_question
  -> answer + list[RetrievedChunk]
  -> score_case
  -> CaseResult
~~~

The evaluator calculates:

- correctness from required patterns or the required refusal;
- citation F1 from generated and expected source IDs;
- retrieval recall from retrieved and human-labelled relevant documents.

## 8. Evaluation persistence

The two SQLite tables have different row granularity:

~~~text
evaluation_runs
  one row per complete evaluate command

evaluation_results
  one row per (run_id, case_id)
~~~

One run with 10 YAML cases creates one <code>evaluation_runs</code> row and 10
<code>evaluation_results</code> rows. Chroma is separate: it stores retrieval
data, while SQLite stores evaluation history.

## 9. Command call paths

~~~text
vantel-qa index
  cli.index_command
  -> config.get_settings
  -> indexer.build_index
  -> loader.load_documents
  -> chunker.chunk_documents
  -> openrouter.embed_texts
  -> indexer.index_chunks
  -> Chroma

vantel-qa search QUESTION
  cli.search_command
  -> config.get_settings
  -> retriever.search_index
  -> openrouter.embed_texts
  -> Chroma query
  -> list[RetrievedChunk]

vantel-qa ask QUESTION
  cli.ask_command
  -> answerer.answer_question
  -> retriever.search_index
  -> answerer.build_context
  -> chat completion
  -> citation validation

vantel-qa evaluate
  cli.evaluate_command
  -> evaluation.run_evaluation
  -> evaluation.load_cases
  -> answerer.answer_question for every case
  -> evaluation.score_case
  -> SQLite persistence
~~~
