import { LibraryNote, Cover } from "../components/LibraryNote.jsx";
import { buildLibraryGroups, getVisibleLibraryPosts, inferCompany, inferRole, normalizeDateLabel, truncateText } from "../domain/posts.js";

export function LibraryPage({ posts, savePosts, library, setLibrary, loadDraft, addDemoPosts }) {
  const groups = buildLibraryGroups(posts);
  const activeCompanyId = library.companyId || groups[0]?.id || "";
  const activeRoleId = library.roleId || "";
  const visible = getVisibleLibraryPosts(groups, activeCompanyId, activeRoleId);
  const activePost = posts.find((post) => post.id === library.activePostId);

  function exportPosts() {
    const blob = new Blob([JSON.stringify(posts, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `offerscope-posts-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function importPosts(file) {
    if (!file) return;
    const text = await file.text();
    const payload = JSON.parse(text);
    const incoming = Array.isArray(payload) ? payload : payload.posts || [];
    await savePosts([...posts, ...incoming]);
  }

  async function deletePost(post) {
    await savePosts(posts.filter((item) => item.id !== post.id));
    setLibrary({ ...library, activePostId: null });
  }

  return (
    <>
      <div className="section-head">
        <h2>帖子库</h2>
        <p className="page-description">顶部按公司切换，例如美团是一组、腾讯是一组；岗位作为公司下面的子标题和筛选标签。</p>
      </div>

      <section className="panel">
        <div className="library-toolbar">
          <div className="library-company-nav">
            {groups.map((group) => (
              <button
                key={group.id}
                type="button"
                className={`library-company-pill ${activeCompanyId === group.id ? "active" : ""}`}
                onClick={() => setLibrary({ ...library, companyId: group.id, roleId: "" })}
              >
                {group.title}
                <strong>{group.count}</strong>
              </button>
            ))}
          </div>
          <div className="actions">
            <button type="button" className="ghost" onClick={addDemoPosts}>
              添加示例
            </button>
            <label className="file-button ghost">
              导入 JSON
              <input type="file" accept="application/json" onChange={(event) => importPosts(event.target.files?.[0])} />
            </label>
            <button type="button" className="ghost" onClick={exportPosts} disabled={!posts.length}>
              导出
            </button>
            <button type="button" className="danger" onClick={() => savePosts([])} disabled={!posts.length}>
              清空帖子库
            </button>
          </div>
        </div>

        {visible.company ? (
          <div className="library-showcase">
            <div className="library-group">
              <div className="library-group-hero">
                <div>
                  <span className="library-feed-kicker">Company</span>
                  <h4>{visible.company.title}</h4>
                  <p>当前公司共 {visible.company.count} 篇帖子，先横向填满展示，再向下扩展。</p>
                </div>
                <div className="library-hero-badges">
                  <span>{visible.company.roles.length} 个岗位方向</span>
                  <span>{visible.posts.length} 篇可见</span>
                </div>
              </div>
              <div className="library-role-tabs">
                <button
                  type="button"
                  className={`library-role-pill ${!activeRoleId ? "active" : ""}`}
                  onClick={() => setLibrary({ ...library, roleId: "" })}
                >
                  全部 <strong>{visible.company.count}</strong>
                </button>
                {visible.company.roles.map((role) => (
                  <button
                    key={role.id}
                    type="button"
                    className={`library-role-pill ${activeRoleId === role.id ? "active" : ""}`}
                    onClick={() => setLibrary({ ...library, roleId: role.id })}
                  >
                    {role.title}
                    <strong>{role.count}</strong>
                  </button>
                ))}
              </div>
              <div className="library-feed">
                {visible.posts.map((post, index) => (
                  <LibraryNote
                    key={post.id}
                    post={post}
                    index={index}
                    onOpen={(item) => setLibrary({ ...library, activePostId: item.id })}
                  />
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">帖子库为空。可以先去采集页搜索，也可以添加示例数据看看交互效果。</div>
        )}
      </section>

      {activePost && (
        <>
          <div className="library-detail-backdrop" onClick={() => setLibrary({ ...library, activePostId: null })} />
          <article className="library-detail-modal">
            <div className="library-detail-visual">
              <Cover post={activePost} company={inferCompany(activePost)} />
            </div>
            <div className="library-detail-panel">
              <header className="library-detail-head">
                <div className="library-note-author large">
                  <span className="library-note-avatar">{activePost.author?.[0] || inferCompany(activePost)[0]}</span>
                  <div>
                    <strong>{activePost.author || "匿名用户"}</strong>
                    <p>{normalizeDateLabel(activePost.publishTime || activePost.collectedAt)}</p>
                  </div>
                </div>
                <div className="library-detail-head-actions">
                  <button type="button" className="library-follow-chip">关注</button>
                  <button type="button" className="ghost" onClick={() => setLibrary({ ...library, activePostId: null })}>关闭</button>
                </div>
              </header>
              <section className="library-detail-content">
                <h3>{activePost.title}</h3>
                <div className="library-detail-tags">
                  <span>{inferCompany(activePost)}</span>
                  <span>{inferRole(activePost)}</span>
                  <span>{activePost.noteTypeLabel || "图文"}</span>
                </div>
                <div className="library-detail-body">
                  {(activePost.content || activePost.excerpt || "暂无正文").split(/\n+/).map((line, index) => (
                    <p key={`${line}-${index}`}>{line}</p>
                  ))}
                </div>
              </section>
              <footer className="library-detail-footer">
                <button type="button" className="ghost" onClick={() => loadDraft(activePost)}>
                  载入采集草稿
                </button>
                <button type="button" className="ghost" onClick={() => navigator.clipboard?.writeText(activePost.content || activePost.excerpt || "")}>
                  复制正文
                </button>
                <button type="button" className="danger" onClick={() => deletePost(activePost)}>
                  删除
                </button>
                <span className="inline-hint">{truncateText(activePost.sourceUrl, 72)}</span>
              </footer>
            </div>
          </article>
        </>
      )}
    </>
  );
}
