import { useState } from "react";
import api, { downloadBlob } from "../api/client";
import FileDropzone from "../components/FileDropzone";
import StatusBanner from "../components/StatusBanner";

interface Structure {
  groups: string[];
  channels: Record<string, string[]>;
  filenames: string[];
}

export default function MergeTab() {
  const [files, setFiles]               = useState<File[]>([]);
  const [structure, setStructure]       = useState<Structure | null>(null);
  const [selectedGroup, setGroup]       = useState("");
  const [selectedChs, setSelectedChs]  = useState<Record<string, boolean>>({});
  const [status, setStatus]             = useState<{type:"info"|"success"|"error";msg:string}|null>(null);
  const [loading, setLoading]           = useState(false);

  const loadStructure = async (dropped: File[]) => {
    setFiles(dropped);
    setStructure(null);
    setStatus(null);
    if (!dropped.length) return;
    setLoading(true);
    try {
      const fd = new FormData();
      for (const f of dropped) fd.append("files", f);
      const res = await api.post("/merge/structure", fd);
      const s: Structure = res.data;
      setStructure(s);
      const grp = s.groups[0] ?? "";
      setGroup(grp);
      const chs: Record<string, boolean> = {};
      for (const ch of (s.channels[grp] ?? [])) chs[ch] = true;
      setSelectedChs(chs);
      setStatus({ type: "success", msg: `${dropped.length} file(s) loaded · ${s.groups.length} group(s)` });
    } catch (e: unknown) {
      setStatus({ type: "error", msg: String((e as {response?:{data?:{detail?:string}}}).response?.data?.detail ?? e) });
    } finally { setLoading(false); }
  };

  const onGroupChange = (g: string) => {
    setGroup(g);
    const chs: Record<string, boolean> = {};
    for (const ch of (structure?.channels[g] ?? [])) chs[ch] = true;
    setSelectedChs(chs);
  };

  const toggleCh = (ch: string) => setSelectedChs((p) => ({ ...p, [ch]: !p[ch] }));

  const convert = async () => {
    const chosen = Object.entries(selectedChs).filter(([,v])=>v).map(([k])=>k);
    if (!chosen.length) { setStatus({type:"error",msg:"Select at least one channel"}); return; }
    setLoading(true);
    setStatus({type:"info",msg:"Converting…"});
    try {
      const fd = new FormData();
      for (const f of files) fd.append("files", f);
      fd.append("group_name", selectedGroup);
      fd.append("selected_channels", JSON.stringify(chosen));
      fd.append("add_time_column", "true");
      fd.append("add_datetime_column", "true");
      const res = await api.post("/merge/convert", fd, { responseType: "blob" });
      downloadBlob(res.data, "cycle_files.zip");
      setStatus({type:"success",msg:"Download started — cycle_files.zip"});
    } catch (e: unknown) {
      setStatus({type:"error",msg:String((e as {response?:{data?:{detail?:string}}}).response?.data?.detail ?? e)});
    } finally { setLoading(false); }
  };

  const channels = structure?.channels[selectedGroup] ?? [];
  const allSel   = channels.every((c) => selectedChs[c]);

  return (
    <div className="max-w-3xl space-y-6">
      <h2 className="text-xl font-semibold text-gray-100">TDMS → Cycle Files</h2>

      <section className="bg-surface rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Step 1 · Upload TDMS Files</h3>
        <FileDropzone onFiles={loadStructure} accept={["tdms"]} current={files.map(f=>f.name)} label="Drop .tdms files here" />
      </section>

      {structure && (
        <>
          <section className="bg-surface rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Step 2 · Select Group & Channels</h3>

            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-400 w-20">Group</label>
              <select value={selectedGroup} onChange={(e)=>onGroupChange(e.target.value)}
                className="bg-gray-800 border border-gray-600 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-blue-500">
                {structure.groups.map(g=><option key={g}>{g}</option>)}
              </select>
            </div>

            <div className="flex gap-2 flex-wrap">
              <button onClick={()=>setSelectedChs(Object.fromEntries(channels.map(c=>[c,true])))}
                className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded">Select All</button>
              <button onClick={()=>setSelectedChs(Object.fromEntries(channels.map(c=>[c,false])))}
                className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded">Deselect All</button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-52 overflow-y-auto">
              {channels.map(ch=>(
                <label key={ch} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                  <input type="checkbox" checked={!!selectedChs[ch]} onChange={()=>toggleCh(ch)} className="accent-blue-500" />
                  {ch}
                </label>
              ))}
            </div>
          </section>

          <button onClick={convert} disabled={loading}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium text-sm transition-colors">
            {loading ? "Converting…" : "Convert & Download ZIP"}
          </button>
        </>
      )}

      {status && <StatusBanner type={status.type} message={status.msg} />}
    </div>
  );
}
