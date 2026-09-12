export default function Diagram({
  label,
  index,
}: {
  label: string;
  index: number;
}) {
  return (
    <figure className="concept-diagram">
      <pre>{label}</pre>
      <figcaption className="technical">
        Concept notation / {String(index + 1).padStart(2, "0")}
      </figcaption>
    </figure>
  );
}
