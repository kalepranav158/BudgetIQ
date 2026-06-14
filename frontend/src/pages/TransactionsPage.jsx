import TransactionsView from "../features/transactions/TransactionsView";

function TransactionsPage() {
  return (
    <section className="page">
      <h1 className="page-title">Transactions</h1>
      <p className="page-subtitle">Review parsed transactions, categories, and subtypes.</p>
      <TransactionsView />
    </section>
  );
}

export default TransactionsPage;
