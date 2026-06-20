# insights/ 挖洞思路库（L3 导航经验）

由 `/learn-writeup` 写入，schema 见项目 CLAUDE.md 第 8 节。

## 目录 = 挖洞阶段（phase）
recon / auth / authz / input / logic / chain。一条思路一个文件，文件名 = id。
跨阶段的思路放“主阶段”目录，其余阶段写进 `also_phases` 字段（不靠目录硬分）。

## 去重键（重要，C1 修正）
**去重键 = `approach`（打法/导航路径），不是 `vuln_root`。**
两条思路即使 vuln_root 相同（如都属 Mass Assignment），只要导航路径不同
（如“翻前端找角色映射” vs “diff create/update 参数”），就是两条独立 insight。
`vuln_root` 降级为标签，仅描述漏洞本质，不参与去重判断。
→ 新文章命中已有 `approach` 才补 case；approach 不同就新建。

## 检索（暂未建工具，约定先行）
当前数量少，人工/AI 直接按目录+文件名浏览。
攒到约 50 条再建 INDEX 自动生成 + 检索 skill；届时检索须“整阶段 trigger 过一遍”，
不可纯关键字匹配（C2）。
