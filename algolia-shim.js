/**
 * TGSOU 本地搜索垫片。
 * 冒充 window.algoliasearch，让原版 SearchWidget.js 无改动地使用本地索引。
 * 索引文件: /search/search-index.json (含常用条目) + /search/chunks/*.json (懒加载)
 */
(function () {
  "use strict";

  var BASE = "/";
  var state = {
    common: null,
    chunkUrls: [],
    all: null,
    loadingAll: null,
  };

  function fetchJson(url) {
    return fetch(url, { credentials: "omit" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status + " for " + url);
      return r.json();
    });
  }

  function loadIndex() {
    return fetchJson(BASE + "search/search-index.json").then(function (data) {
      state.common = data.common || [];
      state.chunkUrls = (data.meta && data.meta.chunks) || [];
      return data;
    });
  }

  function loadAll() {
    if (state.all) return Promise.resolve(state.all);
    if (state.loadingAll) return state.loadingAll;
    state.loadingAll = loadIndex()
      .then(function () {
        return Promise.all(state.chunkUrls.map(fetchJson));
      })
      .then(function (chunks) {
        var extra = [];
        chunks.forEach(function (c) {
          if (Array.isArray(c)) extra = extra.concat(c);
        });
        state.all = state.common.concat(extra);
        return state.all;
      })
      .catch(function (err) {
        console.error("[TGSOU] 索引加载失败:", err);
        state.loadingAll = null;
        return state.common || [];
      });
    return state.loadingAll;
  }

  // ---- 检索与打分 ----
  function score(doc, terms) {
    var s = 0;
    var title = doc.t.toLowerCase();
    var desc = (doc.d || "").toLowerCase();
    for (var i = 0; i < terms.length; i++) {
      var term = terms[i];
      if (!term) continue;
      var ti = title.indexOf(term);
      var di = desc.indexOf(term);
      if (ti === -1 && di === -1) return 0;
      if (ti === 0) s += 120;
      else if (ti > 0) s += 60;
      if (di >= 0) s += 10;
      if (title === term) s += 80;
    }
    return s;
  }

  function localSearch(query) {
    var terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var pool = state.all || state.common || [];
    var hits = [];
    for (var i = 0; i < pool.length; i++) {
      var sc = score(pool[i], terms);
      if (sc > 0) hits.push([sc, pool[i]]);
    }
    hits.sort(function (a, b) {
      return b[0] - a[0];
    });
    return hits.slice(0, 30).map(function (pair) {
      var d = pair[1];
      var url = d.u;
      // 用详情页的类型徽标重建标题后缀，供 SearchWidget 清洗并显示类型徽标
      var type = d.ty || "";
      return {
        title: type ? d.t + " - Telegram" + type + " | TGSOU" : d.t + " | TGSOU",
        url: url,
        _type: type,
        _category: d.c || "",
        _username: d.id,
      };
    });
  }

  // ---- 冒充 algoliasearch API ----
  function ShimIndex() {}

  ShimIndex.prototype.search = function (query) {
    var self = this;
    return loadAll().then(function () {
      var hits = localSearch(query);
      return { hits: hits, nbHits: hits.length, page: 0, query: query };
    });
  };

  function ShimClient() {}
  ShimClient.prototype.initIndex = function () {
    return new ShimIndex();
  };
  // 兼容可能用到的其他方法
  ShimClient.prototype.search = function (queries) {
    return loadAll().then(function () {
      var arr = Array.isArray(queries) ? queries : [queries];
      var results = arr.map(function (q) {
        var hits = localSearch(q.query || q);
        return { hits: hits, nbHits: hits.length, query: q.query || q };
      });
      return { results: results };
    });
  };

  window.algoliasearch = function () {
    return new ShimClient();
  };

  // 预热：页面空闲时拉取全量索引，首次搜索即无延迟
  var warmed = false;
  function warm() {
    if (warmed) return;
    warmed = true;
    loadAll();
  }
  if ("requestIdleCallback" in window) {
    requestIdleCallback(warm, { timeout: 4000 });
  } else {
    setTimeout(warm, 2500);
  }

  console.log("[TGSOU] Local search shim active (no Algolia).");
})();
