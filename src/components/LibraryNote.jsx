import { useEffect, useState } from "react";
import { inferCompany, inferRole, normalizeDateLabel, truncateText } from "../domain/posts.js";

const palette = [
  ["#fff9ec", "#ff9f1a", "#6f4b14"],
  ["#f1f7ff", "#2488ff", "#163a5c"],
  ["#fff4f6", "#ff2442", "#5f1e2a"],
  ["#f4fff9", "#18a058", "#1f5a3a"],
];

export function LibraryNote({ post, index = 0, onOpen }) {
  const [bg, accent, text] = palette[index % palette.length];
  const sizeClass = index % 5 === 0 ? "tall" : index % 3 === 0 ? "compact" : "regular";
  const company = inferCompany(post);

  return (
    <article
      className={`library-note-card ${sizeClass}`}
      style={{
        "--note-card-bg": "#fff",
        "--note-cover-bg": bg,
        "--note-accent": accent,
        "--note-cover-text": text,
        "--note-accent-soft": `${accent}22`,
      }}
    >
      <button className="library-note-open" type="button" onClick={() => onOpen(post)}>
        <Cover post={post} company={company} />
        <div className="library-note-copy">
          <h4>{post.title}</h4>
          <p className="library-note-role">{inferRole(post)}</p>
          <p className="library-note-excerpt">{truncateText(post.content || post.excerpt, 92)}</p>
        </div>
      </button>
      <div className="library-note-meta-row">
        <div className="library-note-author">
          <span className="library-note-avatar">{post.author?.[0] || company[0] || "O"}</span>
          <div>
            <strong>{post.author || "匿名用户"}</strong>
            <p>{normalizeDateLabel(post.publishTime || post.collectedAt)}</p>
          </div>
        </div>
        <span className="library-note-detail-trigger">喜欢 {post.likeCount || 0}</span>
      </div>
    </article>
  );
}

export function Cover({ post, company }) {
  const [imageFailed, setImageFailed] = useState(false);
  const src = post.coverUrl || "";

  useEffect(() => {
    setImageFailed(false);
  }, [src]);

  if (src && !imageFailed) {
    return (
      <div className="library-note-cover has-image">
        <img
          src={src}
          alt={post.title}
          className="react-note-image"
          referrerPolicy="no-referrer"
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      </div>
    );
  }

  return <PlaceholderCover post={post} company={company} reason={src ? "图片加载失败" : "暂无图片"} />;
}

export function PlaceholderCover({ post, company, reason = "暂无图片" }) {
  return (
    <div className="library-note-cover">
      <div className="library-note-cover-top">
        <span>Notes</span>
        <span>{post.noteTypeLabel || reason}</span>
      </div>
      <div className="library-note-cover-body">
        <span className="library-note-company-chip">{company}</span>
        <h4>{post.title}</h4>
        <p>{normalizeDateLabel(post.publishTime || post.collectedAt)}</p>
      </div>
      <div className="library-note-cover-mark">OS</div>
    </div>
  );
}
