import { useDropzone } from "react-dropzone";

interface Props {
  onFiles: (files: File[]) => void;
  accept?: string[];
  multiple?: boolean;
  label?: string;
  current?: string[];
}

export default function FileDropzone({ onFiles, accept, multiple = true, label, current }: Props) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onFiles,
    accept: accept ? Object.fromEntries(accept.map((ext) => [getMime(ext), [`.${ext}`]])) : undefined,
    multiple,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
        isDragActive ? "border-blue-400 bg-blue-950/30" : "border-gray-600 hover:border-gray-500"
      }`}
    >
      <input {...getInputProps()} />
      <p className="text-gray-400 text-sm">
        {isDragActive ? "Drop files here…" : (label ?? "Drag & drop files here, or click to select")}
      </p>
      {current && current.length > 0 && (
        <ul className="mt-2 text-xs text-gray-500 space-y-0.5">
          {current.map((n) => <li key={n}>{n}</li>)}
        </ul>
      )}
    </div>
  );
}

function getMime(ext: string): string {
  const map: Record<string, string> = {
    txt: "text/plain", log: "text/plain", dat: "text/plain",
    csv: "text/csv", tsv: "text/tab-separated-values",
    tdms: "application/octet-stream", json: "application/json",
    xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  };
  return map[ext.toLowerCase()] ?? "application/octet-stream";
}
