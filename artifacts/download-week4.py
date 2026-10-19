import json
from pathlib import Path
import requests

state=json.loads(Path("storage_state.json").read_text(encoding="utf-8"))
cookies={c["name"]:c["value"] for c in state["cookies"] if "thanglong.edu.vn" in c.get("domain","")}
urls={
"TieuChiCham_Cau1_Word.pdf":"https://elearning.thanglong.edu.vn/pluginfile.php/426059/mod_assign/intro/TieuChiCham_Cau1_Word.pdf?time=1751989820445",
"BaiLam_LuyenTap_BaiSo1.docx":"https://elearning.thanglong.edu.vn/pluginfile.php/426059/mod_assign/intro/BaiLam_LuyenTap_BaiSo1.docx",
"ThamKhao_LuyenTap_BaiSo1.pdf":"https://elearning.thanglong.edu.vn/pluginfile.php/426059/mod_assign/intro/ThamKhao_LuyenTap_BaiSo1.pdf",
"Picture_De1.jpg":"https://elearning.thanglong.edu.vn/pluginfile.php/426059/mod_assign/intro/Picture_De1.jpg",
}
out=Path("artifacts/week4"); out.mkdir(parents=True,exist_ok=True)
for name,url in urls.items():
    r=requests.get(url,cookies=cookies,timeout=60)
    r.raise_for_status()
    (out/name).write_bytes(r.content)
    print(name,len(r.content),r.headers.get("content-type"))
