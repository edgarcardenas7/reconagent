from reconagent.models import FinancePolicy, PolicyChunk
from reconagent.services.embeddings import local_text_embedding
from reconagent.services.imports import import_policies
from reconagent.services.policies import PolicyRetriever, policy_query_for_exception


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


def test_policy_retrieval_prefers_explicit_business_terms_over_vector_noise(db_session):
    query = "changed bank account mismatch"
    unrelated = FinancePolicy(
        title="Office expenses",
        body="Team lunches and travel receipts require monthly manager review.",
        risk_level="low",
    )
    relevant = FinancePolicy(
        title="Bank account controls",
        body="Changed bank accounts must be escalated to a controller before payment.",
        risk_level="high",
    )
    db_session.add_all([unrelated, relevant])
    db_session.flush()

    db_session.add_all(
        [
            PolicyChunk(
                policy_id=unrelated.id,
                chunk_text=unrelated.body,
                embedding_json=str(local_text_embedding(query)),
            ),
            PolicyChunk(
                policy_id=relevant.id,
                chunk_text=relevant.body,
                embedding_json=str([0.0] * 64),
            ),
        ]
    )
    db_session.commit()

    citation = PolicyRetriever().retrieve(db_session, query)

    assert "Changed bank accounts" in citation.text


def test_exception_policy_query_adds_domain_terms_for_missing_po(db_session):
    import_policies(
        db_session,
        b"title,body,risk_level\n"
        b"Duplicate payment policy,Duplicate payments inside seven days must be held for review. The controller must verify vendor invoice number payment reference and bank account before release.,high\n"
        b"PO policy,Invoices without purchase orders require a document request before payment.,medium\n",
    )

    query = policy_query_for_exception(
        "missing_po",
        "Invoice INV-002 has no purchase order number.",
    )
    citation = PolicyRetriever().retrieve(db_session, query)

    assert "purchase orders" in citation.text


def test_exception_policy_query_adds_domain_terms_for_changed_bank_account(db_session):
    import_policies(
        db_session,
        b"title,body,risk_level\n"
        b"Duplicate payment policy,Duplicate payments inside seven days must be held for review. The controller must verify vendor invoice number payment reference and bank account before release.,high\n"
        b"Bank account policy,Changed vendor bank accounts are high risk and must be escalated to the controller before payment.,high\n",
    )

    query = policy_query_for_exception(
        "changed_bank_account",
        "Vendor bank account differs between invoice INV-002 and payment.",
    )
    citation = PolicyRetriever().retrieve(db_session, query)

    assert "Changed vendor bank accounts" in citation.text
