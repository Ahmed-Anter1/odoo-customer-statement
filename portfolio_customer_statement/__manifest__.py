{
    "name": "Portfolio Customer Statement",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Generate customer statements with running balances and Excel export",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": ["security/ir.model.access.csv", "wizard/customer_statement_views.xml"],
    "external_dependencies": {"python": ["xlsxwriter"]},
    "installable": True,
}
