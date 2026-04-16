interface Props {
  type: "info" | "success" | "error" | "warning";
  message: string;
}

const styles = {
  info:    "bg-blue-950 border-blue-700 text-blue-300",
  success: "bg-green-950 border-green-700 text-green-300",
  error:   "bg-red-950  border-red-700  text-red-300",
  warning: "bg-yellow-950 border-yellow-700 text-yellow-300",
};

export default function StatusBanner({ type, message }: Props) {
  return (
    <div className={`border rounded-lg px-4 py-3 text-sm ${styles[type]}`}>
      {message}
    </div>
  );
}
