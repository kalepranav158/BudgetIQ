function Skeleton({ rows = 4 }) {
  return (
    <div className="skeleton" aria-hidden="true">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="skeleton__row" key={index} />
      ))}
    </div>
  );
}

export default Skeleton;
