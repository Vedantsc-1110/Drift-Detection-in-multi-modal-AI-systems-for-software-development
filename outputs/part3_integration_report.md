# Part 3 integration run report (§11.1)

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

- Wall-clock: 1.90s
- Query accuracy: 10/10 (metric: 9/10) — PASS
  - order_services: PASS -> [['approveOrder'], ['cancelOrder'], ['findOrders']]
  - invoice_io: PASS -> [['invoiceId'], ['invoiceTypeId']]
  - dags_for_findorders: PASS -> [['orders_etl']]
  - policies_for_invoice: PASS -> [['createInvoice requires manager approval']]
  - contracts_for_order: PASS -> [['Order Agreement']]
  - low_confidence: PASS -> []
  - tasks_for_findorders: PASS -> [['Archive calling findOrders'], ['Nightly sync calling findOrders']]
  - order_entities: PASS -> [['OrderHeader'], ['OrderItem']]
  - order_contract_clauses: FAIL -> [['Fulfilment'], ['Parties']]
  - filing_modules: PASS -> [['ACME-F2025', 'Accounting'], ['ACME-F2025', 'Order'], ['ACME-F2025', 'Party'], ['ACME-F2026', 'Order']]
- Bridge edges: 20/20 verified (metric: 20) — PASS

## Machine spec
- system: Windows
- release: 11
- version: 10.0.26200
- machine: AMD64
- processor: Intel64 Family 6 Model 154 Stepping 4, GenuineIntel
- cpu_count: 12
- ram: 16068 MiB total

## Deviation notes
- Fixture scale: individuals are generated from review tables in
  tests/test_part3_integration.py; real Part 1/2 outputs plug in
  unchanged via ContractStore.load_directory + insert_bridges.
