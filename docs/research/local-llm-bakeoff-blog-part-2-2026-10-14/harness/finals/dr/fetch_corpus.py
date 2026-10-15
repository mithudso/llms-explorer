import urllib.request, re, json, os, html, sys
from html.parser import HTMLParser
URLS = {
 "wiki-specdec":"https://en.wikipedia.org/wiki/Speculative_decoding",
 "wiki-kvcache":"https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
 "arxiv-leviathan":"https://arxiv.org/html/2211.17192",
 "arxiv-medusa":"https://arxiv.org/html/2401.10774",
 "arxiv-eagle":"https://arxiv.org/html/2401.15077",
 "arxiv-pagedattn":"https://arxiv.org/pdf/2309.06180",
 "arxiv-flashattn":"https://arxiv.org/html/2205.14135",
 "arxiv-h2o":"https://arxiv.org/html/2306.14048",
 "arxiv-kivi":"https://arxiv.org/html/2402.02750",
 "arxiv-streamingllm":"https://arxiv.org/html/2309.17453",
 "gh-llamacpp-spec":"https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/speculative.md",
 "vllm-specdec":"https://docs.vllm.ai/en/latest/features/speculative_decoding/",
 "vllm-prefixcache":"https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/",
}
class T(HTMLParser):
    def __init__(s): super().__init__(); s.o=[]; s.skip=0
    def handle_starttag(s,t,a):
        if t in("script","style","nav","footer","header","svg","noscript"): s.skip+=1
        if t in("p","div","br","li","h1","h2","h3","h4","tr"): s.o.append("\n")
    def handle_endtag(s,t):
        if t in("script","style","nav","footer","header","svg","noscript") and s.skip: s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.o.append(d)
def totext(raw, url):
    if url.endswith(".md"): return raw
    p=T(); p.feed(raw); t=html.unescape("".join(p.o)); t=re.sub(r"[ \t]+"," ",t); t=re.sub(r"\n\s*\n+","\n\n",t); return t.strip()
os.makedirs("corpus",exist_ok=True); idx={}
for k,u in URLS.items():
    try:
        rq=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 llm-bench"}); b=urllib.request.urlopen(rq,timeout=60).read()
        if u.endswith("2309.06180"):
            open("/tmp/pa.pdf","wb").write(b); import subprocess; t=subprocess.run(["pdftotext","-layout","/tmp/pa.pdf","-"],capture_output=True,text=True).stdout
        else: t=totext(b.decode("utf-8","ignore"),u)
        words=t.split(); t=" ".join(words[:7000]) if len(words)>7000 else t
        open(f"corpus/{k}.txt","w").write(t); idx[k]={"url":u,"words":len(t.split())}; print("OK",k,len(t.split()))
    except Exception as e: print("FAIL",k,e)
json.dump(idx,open("corpus/index.json","w"),indent=1)
