import { useState } from "react";
import api from "../api/client";
import FileDropzone from "../components/FileDropzone";
import StatusBanner from "../components/StatusBanner";
import PlotlyChart from "../components/PlotlyChart";

export default function CycleViewerTab() {
  const [files, setFiles]       = useState<File[]>([]);
  const [headers, setHeaders]   = useState<string[]>([]);
  const [fileCount, setFileCount] = useState(0);
  const [timeCol, setTimeCol]   = useState("");
  const [ptankCol, setPtankCol] = useState("");
  const [tskinCol, setTskinCol] = useState("");
  const [rightCols, setRightCols] = useState<Record<string,boolean>>({});
  const [mode, setMode]         = useState<"per_cycle"|"duration">("per_cycle");
  const [fileIndex, setFileIndex] = useState(0);
  const [figure, setFigure]     = useState<unknown|null>(null);
  const [loading, setLoading]   = useState(false);
  const [status, setStatus]     = useState<{type:"info"|"success"|"error";msg:string}|null>(null);

  const loadFiles = async (dropped: File[]) => {
    setFiles(dropped);setFigure(null);
    if(!dropped.length) return;
    try {
      const fd = new FormData();
      for(const f of dropped) fd.append("files",f);
      const res = await api.post("/cycle-viewer/headers",fd);
      const hdrs:string[] = res.data.headers;
      setHeaders(hdrs);setFileCount(res.data.file_count);
      const hl=hdrs.map(h=>h.toLowerCase());
      setTimeCol(hdrs[hl.findIndex(h=>h.includes("time"))]??hdrs[0]??"");
      setPtankCol(hdrs[hl.findIndex(h=>h.includes("ptank"))]??"");
      setTskinCol(hdrs[hl.findIndex(h=>h.includes("tskin")||h.includes("tfluid"))]??"");
      const rc:Record<string,boolean>={};
      const tskin=hdrs.find(h=>h.toLowerCase().includes("tskin")||h.toLowerCase().includes("tfluid"))||"";
      if(tskin) rc[tskin]=true;
      setRightCols(rc);
      setStatus({type:"success",msg:`${dropped.length} file(s) · ${hdrs.length} columns`});
    } catch(e:unknown){setStatus({type:"error",msg:String((e as {response?:{data?:{detail?:string}}}).response?.data?.detail??e)});}
  };

  const fetch = async (idx?:number) => {
    const fi = idx ?? fileIndex;
    setLoading(true);setStatus({type:"info",msg:"Loading…"});
    try {
      const fd = new FormData();
      for(const f of files) fd.append("files",f);
      fd.append("config_json",JSON.stringify({
        time_col:timeCol, ptank_col:ptankCol, tskin_col:tskinCol,
        right_cols: Object.entries(rightCols).filter(([,v])=>v).map(([k])=>k),
        mode, file_index:fi,
      }));
      fd.append("file_index",String(fi));
      const res = await api.post("/cycle-viewer/figure",fd);
      setFigure(res.data.figure);
      setStatus({type:"success",msg:`Showing: ${res.data.current_file}`});
    } catch(e:unknown){setStatus({type:"error",msg:String((e as {response?:{data?:{detail?:string}}}).response?.data?.detail??e)});}
    finally{setLoading(false);}
  };

  const nav = (dir:number) => {
    const next=Math.max(0,Math.min(fileCount-1,fileIndex+dir));
    setFileIndex(next);fetch(next);
  };

  return (
    <div className="max-w-5xl space-y-6">
      <h2 className="text-xl font-semibold text-gray-100">Cycle Viewer</h2>

      <section className="bg-surface rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Step 1 · Upload Cycle Files</h3>
        <FileDropzone onFiles={loadFiles} accept={["txt","log","dat","csv"]} current={files.map(f=>f.name)} />
      </section>

      {headers.length>0 && (
        <>
          <section className="bg-surface rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Step 2 · Configure</h3>
            <div className="grid grid-cols-3 gap-3">
              {[["Time",timeCol,setTimeCol],["Ptank (left)",ptankCol,setPtankCol],["Tskin (right)",tskinCol,setTskinCol]].map(([lbl,val,set])=>(
                <div key={String(lbl)}>
                  <label className="text-xs text-gray-400 block mb-1">{String(lbl)}</label>
                  <select value={String(val)} onChange={e=>(set as (v:string)=>void)(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-blue-500">
                    <option value="">— none —</option>
                    {headers.map(h=><option key={h}>{h}</option>)}
                  </select>
                </div>
              ))}
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Additional right-axis columns</label>
              <div className="flex flex-wrap gap-3">
                {headers.map(h=>(
                  <label key={h} className="flex items-center gap-1 text-sm text-gray-300 cursor-pointer">
                    <input type="checkbox" checked={!!rightCols[h]} onChange={e=>setRightCols(p=>({...p,[h]:e.target.checked}))} className="accent-blue-500" />
                    {h}
                  </label>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              {["per_cycle","duration"].map(m=>(
                <label key={m} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                  <input type="radio" name="cv_mode" value={m} checked={mode===m} onChange={()=>setMode(m as typeof mode)} className="accent-blue-500" />
                  {m==="per_cycle"?"Per Cycle":"Full Duration"}
                </label>
              ))}
            </div>
          </section>

          <div className="flex gap-3 items-center">
            <button onClick={()=>fetch()} disabled={loading}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium text-sm">
              {loading?"Loading…":"Load Chart"}
            </button>
            {mode==="per_cycle" && figure && (
              <>
                <button onClick={()=>nav(-1)} disabled={fileIndex===0||loading}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded-lg text-sm">◀ Prev</button>
                <span className="text-sm text-gray-400">{fileIndex+1} / {fileCount}</span>
                <button onClick={()=>nav(1)} disabled={fileIndex>=fileCount-1||loading}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded-lg text-sm">Next ▶</button>
              </>
            )}
          </div>
        </>
      )}

      {figure && <PlotlyChart figure={figure as {data:Plotly.Data[];layout:Partial<Plotly.Layout>}} />}
      {status && <StatusBanner type={status.type} message={status.msg} />}
    </div>
  );
}
