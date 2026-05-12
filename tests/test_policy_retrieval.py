from reconagent.services.embeddings import local_text_embedding
from reconagent.services.imports import import_policies
from reconagent.services.policies import PolicyRetriever


def test_policy_retrieval_uses_stored_embeddings(db_session):
    import_policies(
        db_session,
        b"title,body,risk_level\n"
        b"Bank controls,Changed bank accounts must be escalated to a controller.,high\n"
        b"PO controls,Missing purchase orders require a document request.,medium\n",
    )

    citation = PolicyRetriever().retrieve(db_session, "changed bank account mismatch")

    assert "Changed bank accounts" in citation.text
    assert citation.score > 0
    assert local_text_embedding(citation.text)
