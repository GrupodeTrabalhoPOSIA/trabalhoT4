function PageLoader() {
  return (
    <div className="page-loader" role="status" aria-live="polite">
      <span className="page-loader__indicator" aria-hidden="true" />
      Carregando…
    </div>
  );
}

export default PageLoader;

