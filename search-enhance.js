/**
 * TGSOU 搜索增强：关键词高亮 + 最近搜索历史。
 * 通过 MutationObserver 监听搜索结果列表，无需改动 SearchWidget。
 * 依赖: #search-input, #suggestions-list, #search-form（与 SearchWidget 共用 DOM）
 */
(function () {
  "use strict";

  var HISTORY_KEY = "tgsou-search-history";
  var MAX_HISTORY = 10;
  var CSS_ID = "tgsou-search-enhance-css";

  // ---------- 样式 ----------
  var css = [
    "mark.tgsou-hl{background:none;color:var(--md-sys-color-primary,#7c9cff);font-weight:700;padding:0;}",
    ".tgsou-history-head{display:flex;align-items:center;justify-content:space-between;padding:10px 16px 4px;font-size:12px;opacity:.65;}",
    ".tgsou-history-clear{border:none;background:none;color:inherit;cursor:pointer;font-size:12px;opacity:.8;padding:2px 4px;}",
    ".tgsou-history-clear:hover{opacity:1;text-decoration:underline;}",
    ".tgsou-history-item{display:flex;align-items:center;gap:10px;padding:9px 16px;cursor:pointer;font-size:14px;}",
    ".tgsou-history-item:hover{background:var(--md-sys-color-surface-container-high,rgba(127,127,127,.08));}",
    ".tgsou-history-item i{opacity:.5;font-size:12px;}",
    ".tgsou-history-item .tgsou-h-del{margin-left:auto;border:none;background:none;color:inherit;opacity:.35;cursor:pointer;padding:2px 6px;}",
    ".tgsou-history-item .tgsou-h-del:hover{opacity:1;color:#e57373;}"
  ].join("\n");

  function injectCss() {
    if (document.getElementById(CSS_ID)) return;
    var style = document.createElement("style");
    style.id = CSS_ID;
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ---------- 工具 ----------
  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
  function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  // ---------- 搜索历史 ----------
  function getHistory() {
    try {
      var raw = localStorage.getItem(HISTORY_KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr.filter(function (x) { return typeof x === "string"; }) : [];
    } catch (e) { return []; }
  }
  function saveHistory(list) {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, MAX_HISTORY))); } catch (e) {}
  }
  function recordQuery(q) {
    if (!q || q.length > 60) return;
    var list = getHistory().filter(function (x) { return x !== q; });
    list.unshift(q);
    saveHistory(list);
  }

  function removeHistoryItem(q) {
    saveHistory(getHistory().filter(function (x) { return x !== q; }));
  }

  // ---------- 结果列表高亮 ----------
  var currentQuery = "";

  function highlightInList() {
    var list = document.getElementById("suggestions-list");
    if (!list || !currentQuery) return;
    var terms = currentQuery.toLowerCase().split(/\s+/).filter(function (t) { return t.length >= 1; });
    if (!terms.length) return;
    var spans = list.querySelectorAll("li.search-result-item a > span:first-child");
    spans.forEach(function (span) {
      if (span.dataset.hlDone === currentQuery) return;
      var raw = span.textContent;
      var lower = raw.toLowerCase();
      var hit = false;
      // 逐项找最浅层匹配区间后统一包裹，避免嵌套 mark
      var ranges = [];
      terms.forEach(function (t) {
        var idx = lower.indexOf(t);
        while (idx !== -1) {
          ranges.push([idx, idx + t.length]);
          idx = lower.indexOf(t, idx + t.length);
        }
      });
      if (!ranges.length) { span.dataset.hlDone = currentQuery; return; }
      ranges.sort(function (a, b) { return a[0] - b[0]; });
      // 合并重叠
      var merged = [ranges[0]];
      for (var i = 1; i < ranges.length; i++) {
        var last = merged[merged.length - 1];
        if (ranges[i][0] <= last[1]) last[1] = Math.max(last[1], ranges[i][1]);
        else merged.push(ranges[i]);
      }
      var html = "", pos = 0;
      merged.forEach(function (r) {
        html += escapeHtml(raw.slice(pos, r[0]));
        html += "<mark class='tgsou-hl'>" + escapeHtml(raw.slice(r[0], r[1])) + "</mark>";
        pos = r[1];
      });
      html += escapeHtml(raw.slice(pos));
      span.innerHTML = html;
      span.dataset.hlDone = currentQuery;
    });
  }

  // ---------- 历史面板 ----------
  function showHistoryPanel() {
    var list = document.getElementById("suggestions-list");
    if (!list) return;
    var history = getHistory();
    if (!history.length) return;
    var html =
      '<li class="tgsou-history-head"><span><i class="fa-solid fa-clock-rotate-left" style="margin-right:6px;opacity:.6;"></i>最近搜索</span>' +
      '<button type="button" class="tgsou-history-clear">清空</button></li>';
    history.forEach(function (q) {
      html +=
        '<li class="tgsou-history-item" data-q="' + escapeHtml(q) + '">' +
        '<i class="fa-solid fa-magnifying-glass"></i><span>' + escapeHtml(q) + "</span>" +
        '<button type="button" class="tgsou-h-del" title="删除该记录" data-q="' + escapeHtml(q) + '">' +
        '<i class="fa-solid fa-xmark"></i></button></li>';
    });
    html += '<li style="border-top:1px solid rgba(136,136,136,.12);margin:6px 0 2px;pointer-events:none;"></li>';
    list.insertAdjacentHTML("afterbegin", html);
  }

  function bindHistoryEvents() {
    var list = document.getElementById("suggestions-list");
    if (!list || list.dataset.historyBound) return;
    list.dataset.historyBound = "1";
    list.addEventListener("click", function (ev) {
      var del = ev.target.closest(".tgsou-h-del");
      if (del) {
        ev.preventDefault();
        ev.stopPropagation();
        removeHistoryItem(del.dataset.q);
        var item = del.closest(".tgsou-history-item");
        if (item) item.remove();
        if (!getHistory().length) {
          var head = list.querySelector(".tgsou-history-head");
          if (head) head.remove();
        }
        return;
      }
      var clear = ev.target.closest(".tgsou-history-clear");
      if (clear) {
        ev.preventDefault();
        ev.stopPropagation();
        saveHistory([]);
        showHistoryPanelOnEmpty();
        return;
      }
      var item = ev.target.closest(".tgsou-history-item");
      if (item) {
        ev.preventDefault();
        var input = document.getElementById("search-input");
        input.value = item.dataset.q;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        // 触发提交（站内搜索）
        var form = document.getElementById("search-form");
        if (form) form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      }
    });
  }

  // 空态时展示历史
  function showHistoryPanelOnEmpty() {
    var list = document.getElementById("suggestions-list");
    if (!list) return;
    var hasResults = list.querySelector("li.search-result-item");
    var hasHistory = list.querySelector(".tgsou-history-item");
    if (!hasResults && !hasHistory && !document.getElementById("search-input").value.trim()) {
      showHistoryPanel();
    }
  }

  // ---------- 输入监听：记录有效查询 ----------
  function bindInput() {
    var input = document.getElementById("search-input");
    var form = document.getElementById("search-form");
    if (!input) return;
    var lastRecorded = "";
    // 输入变化：更新 currentQuery（防抖记录）
    var timer = null;
    input.addEventListener("input", function () {
      currentQuery = input.value.trim();
      if (timer) clearTimeout(timer);
      if (currentQuery.length >= 2 && currentQuery !== lastRecorded) {
        timer = setTimeout(function () {
          recordQuery(currentQuery);
          lastRecorded = currentQuery;
        }, 900);
      }
      if (!currentQuery) {
        // 清空输入 → 显示历史
        setTimeout(showHistoryPanelOnEmpty, 250);
      }
    });
    if (form) {
      form.addEventListener("submit", function () {
        var q = input.value.trim();
        if (q) recordQuery(q);
      });
    }
  }

  // ---------- 搜索触发监听：SearchWidget 打开/关闭弹窗 ----------
  function bindModal() {
    var modal = document.getElementById("search-modal");
    if (!modal) return;
    new MutationObserver(function () {
      if (modal.classList.contains("active")) {
        showHistoryPanelOnEmpty();
      }
    }).observe(modal, { attributes: true, attributeFilter: ["class"] });
  }

  // ---------- 结果列表监听：渲染后自动高亮 ----------
  function bindList() {
    var list = document.getElementById("suggestions-list");
    if (!list) return;
    new MutationObserver(function () {
      if (list.querySelector("li.search-result-item")) {
        highlightInList();
      }
    }).observe(list, { childList: true });
  }

  function init() {
    injectCss();
    bindList();
    bindHistoryEvents();
    bindInput();
    bindModal();
    console.log("[TGSOU] Search enhance active (highlight + history).");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
