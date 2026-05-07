import { useEffect, useMemo, useState } from "react";
import { Shell } from "../components/Shell.jsx";
import { AnalysisPage } from "../pages/AnalysisPage.jsx";
import { AgentPage } from "../pages/AgentPage.jsx";
import { CollectPage } from "../pages/CollectPage.jsx";
import { LibraryPage } from "../pages/LibraryPage.jsx";
import { LLMPage } from "../pages/LLMPage.jsx";
import { bootstrap, clearLegacyData, importLegacyData, persistLLMConfig, persistPosts, persistXhsConfig } from "../api/storage.js";
import { analyzePosts } from "../domain/analysis.js";
import { createDefaultLLMConfig, normalizeLLMConfig } from "../domain/modelPresets.js";
import {
  buildLibraryGroups,
  clearLegacyStorage,
  createDefaultCollectForm,
  createDefaultXhsConfig,
  hasLegacyStorage,
  makeDemoPosts,
  mergePostRecords,
  readLegacyStorageSnapshot,
} from "../domain/posts.js";

const ROUTES = new Set(["collect", "library", "analysis", "llm", "agent"]);

export default function App() {
  const [route, setRouteState] = useState(readRoute());
  const [runtime, setRuntime] = useState({ bootstrapping: true, error: "", storage: null });
  const [posts, setPosts] = useState([]);
  const [form, setForm] = useState(createDefaultCollectForm);
  const [xhsConfig, setXhsConfigState] = useState(createDefaultXhsConfig);
  const [llmConfig, setLLMConfigState] = useState(createDefaultLLMConfig);
  const [collect, setCollect] = useState({
    results: [],
    rawCount: 0,
    selectedIds: {},
    loading: false,
    loadingDetailId: "",
    activeCandidate: null,
    status: "准备就绪。",
  });
  const [library, setLibrary] = useState({ companyId: "", roleId: "", activePostId: null });
  const [analysisState, setAnalysisState] = useState({ loading: false, status: "", topicBank: null });
  const [llmState, setLLMState] = useState({
    question: "Redis 扣减库存如何保证数据库和缓存一致？",
    loading: false,
    status: "",
    result: null,
  });

  useEffect(() => {
    const handleHashChange = () => setRouteState(readRoute());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    async function start() {
      try {
        let data = await bootstrap();
        const legacy = readLegacyStorageSnapshot();
        if (!data.storage?.legacyImportCompleted && hasLegacyStorage(legacy)) {
          await importLegacyData(legacy);
          clearLegacyStorage();
          clearLegacyData();
          data = await bootstrap();
        }
        setPosts(mergePostRecords(data.posts || []));
        setXhsConfigState({ ...createDefaultXhsConfig(), ...(data.settings?.xhsConfig || {}) });
        setLLMConfigState(normalizeLLMConfig(data.settings?.llmConfig || {}));
        setRuntime({ bootstrapping: false, error: "", storage: data.storage });
      } catch (error) {
        setRuntime({ bootstrapping: false, error: error.message, storage: null });
      }
    }
    start();
  }, []);

  useEffect(() => {
    if (runtime.bootstrapping) return;
    persistXhsConfig(xhsConfig).catch((error) => setCollect((current) => ({ ...current, status: error.message })));
  }, [xhsConfig, runtime.bootstrapping]);

  useEffect(() => {
    if (runtime.bootstrapping) return;
    persistLLMConfig(llmConfig).catch((error) => setLLMState((current) => ({ ...current, status: error.message })));
  }, [llmConfig, runtime.bootstrapping]);

  function setRoute(nextRoute) {
    window.location.hash = `/${nextRoute}`;
    setRouteState(nextRoute);
  }

  async function savePosts(nextPosts) {
    const merged = mergePostRecords(nextPosts);
    const data = await persistPosts(merged);
    setPosts(data.posts || merged);
    setRuntime((current) => ({
      ...current,
      storage: current.storage ? { ...current.storage, postCount: data.count ?? merged.length } : current.storage,
    }));
  }

  function loadDraft(post) {
    setForm({
      company: post.company || "",
      role: post.role || "",
      keyword: post.keyword || `${post.company || ""} ${post.role || ""} 面经`.trim(),
      page: 1,
    });
    setLibrary({ ...library, activePostId: null });
    setRoute("collect");
  }

  async function addDemoPosts() {
    await savePosts([...posts, ...makeDemoPosts()]);
  }

  const groups = useMemo(() => buildLibraryGroups(posts), [posts]);
  const analysis = useMemo(() => analyzePosts(posts, { company: library.companyId, role: library.roleId }), [posts, library.companyId, library.roleId]);
  const summary = useMemo(() => ({ postCount: posts.length, companyCount: groups.length }), [posts.length, groups.length]);

  if (runtime.error) {
    return (
      <div className="app-shell">
        <section className="panel">
          <h2>启动失败</h2>
          <p className="failed-box">{runtime.error}</p>
          <p className="inline-hint">请确认本地 Python 服务已经启动，或者使用 README 中更新后的启动方式。</p>
        </section>
      </div>
    );
  }

  return (
    <Shell route={route} setRoute={setRoute} summary={summary} runtime={runtime}>
      {route === "collect" && (
        <CollectPage
          form={form}
          setForm={setForm}
          xhsConfig={xhsConfig}
          setXhsConfig={setXhsConfigState}
          collect={collect}
          setCollect={setCollect}
          posts={posts}
          savePosts={savePosts}
        />
      )}
      {route === "library" && (
        <LibraryPage
          posts={posts}
          savePosts={savePosts}
          library={library}
          setLibrary={setLibrary}
          loadDraft={loadDraft}
          addDemoPosts={addDemoPosts}
        />
      )}
      {route === "analysis" && (
        <AnalysisPage
          analysis={analysis}
          llmConfig={llmConfig}
          analysisState={analysisState}
          setAnalysisState={setAnalysisState}
        />
      )}
      {route === "llm" && (
        <LLMPage
          llmConfig={llmConfig}
          setLLMConfig={setLLMConfigState}
          llmState={llmState}
          setLLMState={setLLMState}
          analysis={analysis}
        />
      )}
      {route === "agent" && (
        <AgentPage
          llmConfig={llmConfig}
          filters={{ company: library.companyId, role: library.roleId }}
        />
      )}
    </Shell>
  );
}

function readRoute() {
  const route = window.location.hash.replace(/^#\/?/, "") || "collect";
  return ROUTES.has(route) ? route : "collect";
}
