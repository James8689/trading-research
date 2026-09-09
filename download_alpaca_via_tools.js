const root="/workspace/scratch/cd484c923e48/trading_research";
const groups={software:["MSFT","AAPL","ORCL","CRM"],semiconductors:["NVDA","AMD","AVGO","QCOM","MU","INTC"],finance:["JPM","BAC","C","WFC","GS","MS"],energy:["XOM","CVX","COP","EOG","SLB"],retail:["AMZN","WMT","TGT","COST","HD","LOW"],industrial:["CAT","DE","HON","GE","RTX","BA"],communication:["META","GOOGL","NFLX","DIS"]};
const pad=n=>String(n).padStart(2,"0");
function regular(t){
 const y=+t.slice(0,4),d=t.slice(0,10),m=+t.slice(11,13)*60+(+t.slice(14,16));
 const mar=8+(7-new Date(Date.UTC(y,2,1)).getUTCDay())%7;
 const nov=1+(7-new Date(Date.UTC(y,10,1)).getUTCDay())%7;
 const off=d>=y+"-03-"+pad(mar)&&d<y+"-11-"+pad(nov)?240:300;
 return m-off>=570&&m-off<960;
}
const existing=await tools.exec_command({cmd:"rg --files trading_research/alpaca_batches",max_output_tokens:5000});
const have=new Set(existing.output.split("\n").map(x=>x.split("/").pop()));
let completed=0,failed=[];
for(const year of [2020,2021,2022,2023,2024,2025]){
 const calname="calendar_"+year+".json";
 if(!have.has(calname)){
   const r=await tools.mcp__codex_apps__alpaca_get_calendar({start_date:year+"-01-01",end_date:year+"-12-31"});
   let d=r.structuredContent;if(!d?.calendar)d=JSON.parse(r.content[0].text);
   if(d.result)d=typeof d.result==="string"?JSON.parse(d.result):d.result;
   if(!d.calendar)throw Error("Calendar missing for "+year);
   await tools.apply_patch("*** Begin Patch\n*** Add File: "+root+"/alpaca_batches/"+calname+"\n+"+JSON.stringify(d)+"\n*** End Patch");
 }
 for(let month=1;month<=12;month++){
   const start=year+"-"+pad(month)+"-01T00:00:00Z";
   const end=(month===12?year+1:year)+"-"+pad(month===12?1:month+1)+"-01T00:00:00Z";
   const tasks=Object.entries(groups).filter(([group])=>!have.has(year+"-"+pad(month)+"_"+group+".json"));
   for(let k=0;k<tasks.length;k+=3){
    const results=await Promise.allSettled(tasks.slice(k,k+3).map(async([group,symbol])=>{
      const name=year+"-"+pad(month)+"_"+group+".json";
      const r=await tools.mcp__codex_apps__alpaca_get_stock_bars({symbol,start,end,timeframe:"5Min",feed:"sip",limit:50000,tz:"UTC"});
      if(r.isError)throw Error(name+": "+(r.content?.[0]?.text||"tool error"));
      const d=r.structuredContent||JSON.parse(r.content[0].text);
      if(r.isError||!d.bars||!d.counts)throw Error(name+": data missing "+JSON.stringify(r).slice(0,200));
      if(d.counts.records>=50000)throw Error(name+": hit requested limit; do not accept truncated batch");
      if(symbol.some(s=>!d.bars[s]?.length))throw Error(name+": missing symbol");
      const p={request:d.request,counts:d.counts,filter:"Regular 09:30 <= ET < 16:00; raw API count includes extended hours; official calendar applied at analysis",columns:["timestamp","open","high","low","close","volume"],bars:Object.fromEntries(Object.entries(d.bars).map(([s,rows])=>[s,rows.filter(b=>regular(b.timestamp)).map(b=>[b.timestamp,b.open,b.high,b.low,b.close,b.volume])]))};
      const w=await tools.apply_patch("*** Begin Patch\n*** Add File: "+root+"/alpaca_batches/"+name+"\n+"+JSON.stringify(p)+"\n*** End Patch");
      have.add(name);completed++;return {name,bars:Object.values(p.bars).reduce((n,a)=>n+a.length,0)};
    }));
    results.forEach((r,i)=>{if(r.status!=="fulfilled")failed.push({year,month,group:tasks[k+i][0],error:String(r.reason)});});
    if(failed.length){notify({failed});break;}
   }
   await tools.exec_command({cmd:"$CODEX_PRIMARY_RUNTIME_PYTHON trading_research/checkpoint.py",max_output_tokens:500});
   if(month%3===0||failed.length)notify({year,through_month:month,new_batches_completed:completed,failed});
   if(failed.length)break;
 }
 const note={stage:failed.length?"download requires retry of failed batches":"download complete through "+year,new_batches_completed:completed,failed,next:"Inspect manifest.json, then resume missing batches. Extended results have not been computed."};
 await tools.apply_patch("*** Begin Patch\n*** Add File: "+root+"/EXTENSION_STATUS.json\n+"+JSON.stringify(note,null,2).replaceAll("\n","\n+")+"\n*** End Patch");
 const save=await tools.exec_command({cmd:"$CODEX_PRIMARY_RUNTIME_PYTHON trading_research/checkpoint.py --save",yield_time_ms:1000,max_output_tokens:1000});
 notify({checkpoint_year:year,...save});
 if(save.session_id){store("checkpoint_pending_session",save.session_id);notify("Checkpoint upload still running; pause downloads to inspect outcome.");break;}
 if(save.exit_code!==0||failed.length)break;
}
text({new_batches_completed:completed,failed});
