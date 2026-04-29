import { useEffect, useState } from "react";
import { PlaceholderCover } from "../components/LibraryNote.jsx";
import { getNoteDetail, searchPosts } from "../api/xhs.js";
import { buildPostFromSearchItem, truncateText } from "../domain/posts.js";

export function CollectPage({ form, setForm, xhsConfig, setXhsConfig, collect, setCollect, posts, savePosts }) {
  const selectedCount = Object.values(collect.selectedIds).filter(Boolean).length;

  async function runSearch(nextPage = form.page) {
    const query = form.keyword.trim();
    if (!query) {
      setCollect({ ...collect, status: "请先填写搜索关键词。" });
      return;
    }
    setCollect({ ...collect, loading: true, status: "正在搜索小红书帖子..." });
    try {
      const data = await searchPosts({
        query,
        cookiesStr: xhsConfig.cookiesStr,
        page: nextPage,
        pageSize: xhsConfig.pageSize,
        sortTypeChoice: xhsConfig.sortTypeChoice,
      });
      setForm({ ...form, page: nextPage });
      setCollect({
        ...collect,
        results: data.items || [],
        rawCount: data.rawCount || 0,
        selectedIds: {},
        loading: false,
        status: `已加载第 ${nextPage} 页，共返回 ${data.items?.length || 0} 条。`,
      });
    } catch (error) {
      setCollect({ ...collect, loading: false, status: error.message });
    }
  }

  async function addSelected() {
    const selected = collect.results.filter((item) => collect.selectedIds[item.noteId || item.sourceUrl || item.title]);
    if (!selected.length) {
      setCollect({ ...collect, status: "请先勾选要入库的帖子。" });
      return;
    }
    const nextPosts = [...posts, ...selected.map((item) => buildPostFromSearchItem(item, form))];
    await savePosts(nextPosts);
    setCollect({ ...collect, status: `已入库 ${selected.length} 篇帖子。`, selectedIds: {} });
  }

  async function loadDetail(item) {
    setCollect({ ...collect, loadingDetailId: item.noteId || item.sourceUrl || item.title, status: "正在拉取候选详情..." });
    try {
      const url = item.sourceUrl;
      const data = await getNoteDetail({ url, cookiesStr: xhsConfig.cookiesStr });
      const merged = { ...item, ...data.item };
      setCollect({
        ...collect,
        loadingDetailId: "",
        activeCandidate: merged,
        results: collect.results.map((result) => (result.noteId === item.noteId ? merged : result)),
        status: "详情已加载。",
      });
    } catch (error) {
      setCollect({ ...collect, loadingDetailId: "", status: error.message, activeCandidate: item });
    }
  }

  function toggleItem(item) {
    const id = item.noteId || item.sourceUrl || item.title;
    setCollect({ ...collect, selectedIds: { ...collect.selectedIds, [id]: !collect.selectedIds[id] } });
  }

  return (
    <>
      <div className="section-head">
        <h2>采集帖子</h2>
        <p className="page-description">填写 Cookie 和搜索条件后，可以刷新、翻页、查看候选详情，并将选中的帖子写入本地 SQLite。</p>
      </div>

      <div className="page-container">
        <section className="panel feature-panel">
          <div className="panel-title">
            <h3>搜索条件</h3>
            <p>公司和岗位会作为入库后的分组信息，搜索关键词可以更自由。</p>
          </div>
          <div className="form-grid">
            <label>
              <span>公司</span>
              <input value={form.company} onChange={(event) => setForm({ ...form, company: event.target.value })} />
            </label>
            <label>
              <span>岗位</span>
              <input value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} />
            </label>
            <label className="full">
              <span>关键词</span>
              <input value={form.keyword} onChange={(event) => setForm({ ...form, keyword: event.target.value })} />
            </label>
            <label className="full">
              <span>小红书 Cookie</span>
              <textarea
                className="small-area"
                value={xhsConfig.cookiesStr}
                onChange={(event) => setXhsConfig({ ...xhsConfig, cookiesStr: event.target.value })}
                placeholder="从浏览器登录态复制 Cookie，用于调用本地采集脚本。"
              />
            </label>
            <label>
              <span>每页数量</span>
              <input
                type="number"
                min="1"
                max="50"
                value={xhsConfig.pageSize}
                onChange={(event) => setXhsConfig({ ...xhsConfig, pageSize: Number(event.target.value) || 20 })}
              />
            </label>
            <label>
              <span>排序</span>
              <select
                value={xhsConfig.sortTypeChoice}
                onChange={(event) => setXhsConfig({ ...xhsConfig, sortTypeChoice: Number(event.target.value) })}
              >
                <option value={0}>综合</option>
                <option value={1}>最新</option>
                <option value={2}>最多点赞</option>
              </select>
            </label>
          </div>
          <div className="actions textarea-wrap">
            <button type="button" disabled={collect.loading} onClick={() => runSearch(1)}>
              搜索帖子
            </button>
            <button type="button" className="ghost" disabled={collect.loading} onClick={() => runSearch(form.page)}>
              刷新本页
            </button>
            <button type="button" className="ghost" disabled={collect.loading || form.page <= 1} onClick={() => runSearch(form.page - 1)}>
              上一页
            </button>
            <button type="button" className="ghost" disabled={collect.loading} onClick={() => runSearch(form.page + 1)}>
              下一页
            </button>
            <button type="button" onClick={addSelected} disabled={!selectedCount}>
              入库已选 {selectedCount}
            </button>
          </div>
          <p className="inline-hint">{collect.status}</p>
        </section>

        <section className="panel">
          <div className="library-feed-head">
            <div>
              <span className="library-feed-kicker">Search Results</span>
              <h4>候选帖子</h4>
              <p>当前第 {form.page} 页，接口原始返回 {collect.rawCount || 0} 条。</p>
            </div>
          </div>
          {collect.results.length ? (
            <div className="search-results-grid">
              {collect.results.map((item) => {
                const id = item.noteId || item.sourceUrl || item.title;
                return (
                  <article key={id} className={`search-card ${collect.selectedIds[id] ? "selected" : ""}`}>
                    <div className="search-card-head">
                      <label className="search-check">
                        <input type="checkbox" checked={Boolean(collect.selectedIds[id])} onChange={() => toggleItem(item)} />
                        选择
                      </label>
                      <span className="search-type">{item.noteTypeLabel || "图文"}</span>
                    </div>
                    <div className="search-card-body">
                      <div className="search-card-media">
                        <CandidateImage item={item} company={form.company} />
                      </div>
                      <div className="search-card-content">
                        <h4>{item.title}</h4>
                        <p className="search-card-meta">{item.author || "匿名用户"} · {item.publishTime || "未知时间"} · ♡ {item.likeCount || 0}</p>
                        <p className="search-card-desc">{truncateText(item.content || item.excerpt, 128)}</p>
                      </div>
                      <div className="card-actions">
                        <button type="button" className="ghost" onClick={() => loadDetail(item)}>
                          {collect.loadingDetailId === id ? "加载中..." : "查看详情"}
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">还没有搜索结果。填好条件后点击“搜索帖子”。</div>
          )}
        </section>
      </div>

      {collect.activeCandidate && (
        <>
          <div className="drawer-mask" onClick={() => setCollect({ ...collect, activeCandidate: null })} />
          <aside className="detail-drawer">
            <div className="detail-drawer-head">
              <div>
                <span className="library-feed-kicker">Candidate</span>
                <h3>{collect.activeCandidate.title}</h3>
              </div>
              <button type="button" className="ghost" onClick={() => setCollect({ ...collect, activeCandidate: null })}>
                关闭
              </button>
            </div>
            <div className="detail-drawer-body">
              <CandidateDetailImage item={collect.activeCandidate} company={form.company} />
              <div className="detail-drawer-content">{collect.activeCandidate.content || collect.activeCandidate.excerpt || "暂无正文"}</div>
            </div>
            <div className="actions">
              <button type="button" onClick={() => savePosts([...posts, buildPostFromSearchItem(collect.activeCandidate, form)])}>
                入库当前帖子
              </button>
            </div>
          </aside>
        </>
      )}
    </>
  );
}

function CandidateImage({ item, company }) {
  const [imageFailed, setImageFailed] = useState(false);
  const src = item.coverUrl || "";

  useEffect(() => {
    setImageFailed(false);
  }, [src]);

  if (src && !imageFailed) {
    return (
      <img
        src={src}
        alt={item.title}
        referrerPolicy="no-referrer"
        loading="lazy"
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <div className="search-card-placeholder rich">
      <strong>{company || "OfferScope"}</strong>
      <span>{src ? "图片加载失败" : "暂无图片"}</span>
    </div>
  );
}

function CandidateDetailImage({ item, company }) {
  const [imageFailed, setImageFailed] = useState(false);
  const src = item.coverUrl || "";

  useEffect(() => {
    setImageFailed(false);
  }, [src]);

  if (src && !imageFailed) {
    return (
      <img
        className="detail-drawer-cover"
        src={src}
        alt={item.title || ""}
        referrerPolicy="no-referrer"
        loading="lazy"
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <div className="detail-drawer-cover fallback-cover">
      <PlaceholderCover post={item} company={company || item.company || "OfferScope"} reason={src ? "图片加载失败" : "暂无图片"} />
    </div>
  );
}
