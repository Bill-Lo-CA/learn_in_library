# Future Suggestions / 未來建議

This document tracks forward-looking ideas for `RAG_workspace`. Each item is written in English first, followed by Traditional Chinese.

本文件追蹤 `RAG_workspace` 的後續方向。每個項目先以英文描述，再提供繁體中文說明。

## Near Term / 近期工作

- Rename the default git branch from `master` to `main`.
  將預設 git 分支從 `master` 改成 `main`。

- Keep the project installable in editable mode for local development.
  讓專案可以用 editable mode 安裝，方便本機開發和其他 sibling projects 引用。

## Retrieval Quality / 檢索品質

- Test several chunk sizes before locking defaults, especially 250-320 words for less diluted embeddings.
  在固定預設值前測試不同 chunk 大小，特別是 250-320 words，避免 embedding 被過多不相關內容稀釋。

- Add a retrieval debug command that shows query text, backend, score, source file, page range, and preview text.
  新增 retrieval debug 指令，顯示 query、backend、分數、來源檔案、頁碼範圍和文字預覽。

- Compare `bge-m3` retrieval against other embedding models such as `qwen3-embedding`, `nomic-embed-text`, or `embeddinggemma`.
  比較 `bge-m3` 和其他 embedding models，例如 `qwen3-embedding`、`nomic-embed-text`、`embeddinggemma`。

- Add Chinese-to-English technical query rewriting for English source corpora.
  對英文來源資料加入中文到英文技術詞的 query rewrite，例如把「訊號反射」擴寫成 `signal reflection`、`impedance discontinuity`、`reflection coefficient`。

- Add hybrid retrieval that combines `bge-m3` vector results with lexical results.
  加入 hybrid retrieval，合併 `bge-m3` vector retrieval 和 lexical retrieval 的候選結果。

- Retrieve a larger candidate set first, such as top 10 or top 20, then rerank down to the final context set.
  先抓較大的候選集合，例如 top 10 或 top 20，再 rerank 成最後要給 LLM 的 context。

- Track retrieval quality by ranking correctness rather than treating vector similarity scores as absolute percentages.
  評估 retrieval 時優先看排名是否正確，而不是把 vector similarity score 當成百分比分數。

## Learning Platform Direction / 學習平台方向

- Evolve the workspace from a plain RAG Q&A tool into a personal technical learning system.
  將 workspace 從單純 RAG 問答工具，逐步發展成個人化技術學習系統。

- Turn uploaded books into a structured learning base: concepts, summaries, examples, quizzes, and review schedules.
  將上傳的書轉成結構化學習資料庫：概念、摘要、例子、測驗和複習排程。

- Build a concept map or lightweight knowledge graph from parsed documents.
  從解析後的文件建立 concept map 或輕量知識圖譜。

- Support multiple explanation levels: beginner, intermediate, and advanced.
  支援不同解釋難度：初學者、中階、進階。

- Generate answers in the user's preferred language while keeping source citations tied to original pages.
  用使用者偏好的語言回答，同時保留原始頁碼引用。

## Personalization / 個人化

- Add a Learning Profile Service to store user preferences and goals.
  新增 Learning Profile Service，記錄使用者偏好與學習目標。

- Track preferred language, explanation style, current level, exam target, weak topics, strong topics, preferred question type, and daily study time.
  追蹤偏好語言、解釋風格、目前程度、考試目標、弱點主題、強項主題、偏好題型和每日學習時間。

- Add a Concept Mastery Engine for per-concept progress tracking.
  新增 Concept Mastery Engine，追蹤每個概念的掌握程度。

- Track concept id, mastery score, wrong count, correct count, last reviewed time, next review time, and confidence level.
  追蹤 concept id、掌握分數、錯誤次數、答對次數、上次複習時間、下次複習時間和信心程度。

- Use user history to decide whether to explain, quiz, review, or deepen a topic.
  根據使用者歷史紀錄決定要解釋、出題、複習，還是深入某個主題。

## Adaptive Quiz And Review / 自適應測驗與複習

- Add an Adaptive Quiz Engine that generates questions based on user state rather than fixed chapter counts.
  新增 Adaptive Quiz Engine，根據使用者狀態出題，而不是固定每章產生固定題數。

- Generate beginner comprehension questions after first reading, scenario questions after strong performance, and comparison or reverse questions for weak concepts.
  初次閱讀後產生基礎理解題；表現好時產生情境題；對弱點概念產生比較題或反向題。

- Support exam-style multiple choice and interview-style explanation questions.
  支援考試風格選擇題與面試風格解釋題。

- Include wrong-option analysis, real-world examples, exam traps, and memory hints.
  為錯誤選項加入分析、真實例子、考試陷阱和記憶提示。

- Split quiz generation and quiz review into separate model roles if quiz quality becomes inconsistent.
  如果題目品質不穩，將出題與審題拆成不同模型角色。

- Add spaced repetition and a wrong-answer notebook.
  加入 spaced repetition 和錯題本。

- Schedule reviews based on wrong concepts, elapsed time, repeated mistakes, and correct streaks.
  根據錯誤概念、間隔時間、重複錯誤和連續答對次數安排複習。

## Learning Path Planning / 學習路徑規劃

- Add an Adaptive Learning Planner that creates learning paths from user goals.
  新增 Adaptive Learning Planner，根據使用者目標建立學習路徑。

- Support paths for certification preparation, interview preparation, quick book understanding, and deep technical study.
  支援證照準備、面試準備、快速理解一本書和深入技術學習等路徑。

- Plan based on user goal, current level, available time, answer history, chapter importance, and weak concepts.
  根據使用者目標、目前程度、可用時間、答題紀錄、章節重要性和弱點概念規劃。

- Allow the system to recommend which chapters or concepts to study next instead of forcing linear reading.
  讓系統推薦下一個要讀的章節或概念，而不是強迫從第一章線性讀到最後一章。

## Evaluation And Observability / 評估與可觀測性

- Log retrieval backend, model name, query, selected chunks, scores, and answer citations.
  記錄 retrieval backend、模型名稱、query、選中的 chunks、分數和回答引用。

- Add answer-quality checks for citation coverage and unsupported claims.
  加入回答品質檢查，確認引用覆蓋率和是否有未被 context 支援的說法。

## Multi-Project Use / 多專案使用

- Expose a stable CLI that sibling projects can call without knowing internal paths.
  提供穩定 CLI，讓同層其他 projects 不需要知道內部路徑也能呼叫。

- Expose a small Python API for direct import from other projects.
  提供小型 Python API，讓其他 projects 可以直接 import。

- Avoid absolute paths in source code and configs.
  避免在 source code 和 config 中寫死絕對路徑。

- Add example corpus configs that can be copied for new books or document sets.
  加入可複製的 corpus config 範例，方便新增不同書籍或文件集。

## GitHub Readiness / GitHub 準備

- Keep source PDFs, generated chunks, generated indexes, and local caches out of git unless explicitly approved.
  除非明確同意，否則不要把來源 PDF、generated chunks、generated indexes 和本地 cache 放進 git。

- Add a license once the project direction is clearer.
  等專案方向更清楚後補上 license。

- Add install instructions for local use and GitHub-based installation.
  加入本機使用和 GitHub 安裝說明。

- Consider Git LFS only if there is a clear reason to version large non-private files.
  只有在確定需要 version 大型且非私有檔案時，才考慮 Git LFS。

## Possible Later Features / 之後可能功能

- Web UI for selecting corpora, asking questions, reviewing citations, and taking quizzes.
  建立 Web UI，支援選擇 corpus、問問題、檢視引用和做測驗。

- Conversation memory per corpus.
  為每個 corpus 加入對話記憶。

- Multiple document support per corpus.
  支援每個 corpus 包含多份文件。

- Incremental re-indexing when files change.
  當文件變更時支援 incremental re-indexing。

- Exportable answer logs with citations.
  匯出含引用的回答紀錄。

- Personalized dashboards for mastery, weak topics, review schedule, and learning path progress.
  建立個人化 dashboard，顯示掌握程度、弱點主題、複習排程和學習路徑進度。
