import { requestJsonCompletion } from "../api/llm.js";
import { buildTopicBankPrompt } from "./analysis.js";

export function buildAnswerPrompt(question, context = "") {
  return `你是中文技术面试辅导助手。请回答下面的问题，要求结构清晰、贴近真实面试表达，并结合项目场景。

问题：
${question}

可参考上下文：
${context || "无"}

请输出 JSON：
{
  "summary": "一句话核心答案",
  "answer": ["分点回答"],
  "pitfalls": ["容易踩坑"],
  "followUps": ["可能被追问的问题"]
}`;
}

export async function generateAnswer(config, question, context) {
  return requestJsonCompletion(config, {
    messages: [
      { role: "system", content: "你只输出合法 JSON，不要输出 Markdown 代码块。" },
      { role: "user", content: buildAnswerPrompt(question, context) },
    ],
    temperature: 0.4,
  });
}

export async function generateTopicBank(config, analysis) {
  return requestJsonCompletion(config, {
    messages: [
      { role: "system", content: "你只输出合法 JSON，不要输出 Markdown 代码块。" },
      {
        role: "user",
        content: `${buildTopicBankPrompt(analysis)}

请输出 JSON：
{
  "groups": [
    {
      "title": "主题名",
      "questions": [
        {"question": "问题", "focus": "考察点", "answerHint": "答题方向"}
      ]
    }
  ]
}`,
      },
    ],
    temperature: 0.35,
  });
}
