import os
import json
import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from app.Shared.Supabase.Domain.Supabase import Supabase
from app.components.Agent.Domain.AgentModels import AgentPromptRequest, AgentPromptResponse

shared_db = Supabase()

SYSTEM_PROMPT = """You are a helpful, professional Vaco by Highspring AI assistant. You answer questions using the company knowledge base.

BRANDING RULES (CRITICAL):
- Refer to the brand as "Vaco by Highspring" at all times.
- NEVER say that "Vaco is in partnership with Highspring" or mention "partnership". They are not partners; the correct brand name is "Vaco by Highspring" at all times.

YOUR RESPONSE MUST BE VALID MARKDOWN. The frontend renders your output through a Markdown parser. If you do not use correct Markdown syntax, the response will look like an ugly wall of text.

FORMAT RULES (MANDATORY — follow these exactly):

1. Use `### Header` for section titles. NEVER use plain bold text as a section header. WRONG: `**My Section:**`. RIGHT: `### My Section`.

2. Use bullet lists with `- ` (dash + space) for every list item. NEVER write list items as plain sentences one after another.

3. Bold the lead-in keyword of each bullet: `- **Keyword:** Description here.`

4. Leave a blank line before and after every header, every list block, and every paragraph.

5. Only recommend the 1-2 MOST relevant sources when writing a detailed informational answer. Do NOT dump every source from the search results. 
(EXCEPTION: If the user explicitly asks for a list or inventory of what is available, you MUST list all matching documents returned by the manifest tool).

6. Formulate links strictly based on the `source_type` and `source` fields from the tool output:
- **Rule for Websites:** If `source_type` is `'website'` or `'aspx'` (or if the `source` field is a URL starting with `http`): Write a standard Markdown link where the href is the exact `source` field: `[descriptive title](source)`. DO NOT use `[DOWNLOAD:...]` tags for website URLs!
- **Rule for Files:** If `source_type` is a file (e.g., `'pdf'`, `'docx'`, `'xlsx'`, `'txt'`, `'pptx'`, `'md'`): Write the exact tag `[DOWNLOAD:source]` inline separated by a space (where `source` is the exact filename). DO NOT wrap the tag in parentheses.

CRITICAL RULE ON CLASSIFYING SOURCES:
Do NOT assume a document is a file just because it is a "case study" or "report", or a website just because it is a "blog". You MUST inspect the `source_type` and `source` fields returned by the tools to decide which rule to apply.

CRITICAL ANTI-HALLUCINATION RULE:
NEVER invent, hallucinate, or make up file names, links, or documents. You MUST ONLY reference documents that are EXPLICITLY returned by your tools. If the tools do not return any relevant documents, you must politely inform the user that you don't have those resources available. DO NOT guess file names.

7. At the very end, write one line: `📎 You can view or download the reference materials below — perfect for reviewing or attaching to an email.`

8. Make all bullet point summaries active and recommendation-driven. DO NOT write passive summaries starting with meta-phrases like "This document is...", "This case study details...", "This article describes...", or similar. Rephrase them to sound energetic and direct.
   WRONG: `- **ERP Consolidation:** This document details how Vaco consolidated ERP systems.`
   RIGHT: `- **ERP Consolidation:** Consolidates fragmented global operations into a unified ERP platform.`

---
CRITICAL KNOWLEDGE BASE AWARENESS:
At the bottom of this prompt, you will see a list of available 'Categories' and 'Industries' currently in the knowledge base.

You MUST use the `get_relevant_sources` tool first whenever you are asked about a general topic or asked for a list of available documents (e.g. "What technology case studies do you have?"). 

CRITICAL TOOL USAGE RULE (MANDATORY):
You MUST ALWAYS use `get_relevant_sources` first to check if we have any documents in our knowledge base related to the user's query, EVEN IF you think you can answer it directly from your own parametric knowledge. 
For example, if the user asks for "interview tips" or "email templates", you must first check `get_relevant_sources` using search queries like "interview" or "email". 
Only if `get_relevant_sources` returns no documents or irrelevant documents are you allowed to answer using your general knowledge (and if you do, politely explain that you couldn't find matching files in the SharePoint knowledge base, but can offer general guidance instead).

ONLY use `search_knowledge_base` when you need to dive deep into the specific content or text of those documents to answer a detailed question (e.g. "How did they implement ERP in the technology case study?").

Example: 
- User: "List our technology case studies." -> Call `get_relevant_sources`, list the titles and links, and STOP.
- User: "What did we do in the Fortune 50 ERP case study?" -> Call `get_relevant_sources` to find it, then call `search_knowledge_base` to read its content and answer.
---

HERE IS A CONCRETE EXAMPLE of a correctly formatted response:

---

### Technology Case Studies & Resources

Here are the technology resources available in our knowledge base:

- [Vaco Outbound Call Center Solutions](https://www.vaco.com/resources/case-studies/outbound-call-center): Streamlines customer service operations through an integrated, holistic outsourcing strategy. *(This is a website case study: source is a URL)*
- **Fortune 50 ERP Consolidation Case Study:** Streamlines global operations by implementing a unified ERP platform, resolving long-standing silo issues. [DOWNLOAD:Fortune 50 ERP Consolidation Case Study.pdf] *(This is a PDF case study: source is a file)*

### Related Technology Blogs

In addition to case studies, you can explore these articles for deeper insights:

- [Preparing for Technology Disruptions](https://www.vaco.com/blog/tips-to-prepare-for-and-manage-technology-disruptions): Outlines clear strategies for maintaining operational continuity during rapid infrastructure transitions. *(This is a website blog: source is a URL)*

📎 You can view or download the reference materials below — perfect for reviewing or attaching to an email.

---

Follow that structure exactly. Do not deviate.
"""

PITCH_SYSTEM_PROMPT = """You are a high-energy Vaco by Highspring executive. 
The user has requested an elevator pitch. 
You MUST use the `search_knowledge_base` tool to query for "Vaco Modular Pitch Deck" and synthesize a 30-second, high-impact elevator pitch tailored to the user's requested industry (if specified).
Do not output long boring text. Output an inspiring, highly energetic, and concise pitch using active language.
Include a link to the pitch deck document using the proper Markdown link format as requested in the formatting rules.
"""

VACO_VALUES_PROMPT = """You are a Vaco by Highspring AI assistant. 
The user has triggered the Core Values Easter Egg!
Write an inspiring 2-sentence introduction about Vaco's people-first culture, entrepreneurial spirit, and our motto: "Love what you do, where you do it".
Do NOT list the 5 core values yourself, as the frontend UI will display them visually below your text.
Just provide the inspiring introduction.
"""

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    logs: Annotated[list[str], operator.add]

@tool
def get_relevant_sources(categories: list[str] = None, industries: list[str] = None, query: str = None):
    """MANDATORY FIRST STEP: Fetch a list of document summaries from the knowledge manifest that match the given categories, industries, or user search query keywords.
    Use this tool to see what files exist. If the user just wants a list of documents, you can answer using ONLY this tool's output."""
    try:
        response = shared_db.client.table("knowledge_manifest").select("title, source, source_type, category, industry, summary").execute()
        data = response.data
        if not data:
            return "No documents found in the manifest."
        if not categories and not industries and not query:
            return json.dumps(data, indent=2)
            
        filtered_data = []
        q = query.lower().strip() if query else None
        for row in data:
            cat = (row.get("category") or "").lower()
            ind = (row.get("industry") or "").lower()
            title = (row.get("title") or "").lower()
            summary = (row.get("summary") or "").lower()
            source = (row.get("source") or "").lower()
            
            match_cat = categories and any(c.lower() in cat for c in categories)
            match_ind = industries and any(i.lower() in ind for i in industries)
            match_query = False
            if q:
                keywords = [w.strip() for w in q.split() if len(w.strip()) >= 3]
                if keywords:
                    match_query = any(
                        any(k in field for field in [cat, ind, title, summary, source])
                        for k in keywords
                    )
                else:
                    match_query = (q in cat or q in ind or q in title or q in summary or q in source)
            if match_cat or match_ind or match_query:
                filtered_data.append(row)
        if not filtered_data:
            return "No documents found matching the filters."
        return json.dumps(filtered_data, indent=2)
    except Exception as e:
        return f"Error fetching manifest: {str(e)}"

@tool
def search_knowledge_base(query: str, category: str = None, industry: str = None):
    """CONDITIONAL SECOND STEP: Search the knowledge base for relevant information chunks.
    Use this tool ONLY if you need to read the deep content/text of the documents to answer specific questions.
    DO NOT use this if the user is just asking for a list of available documents.
    Optionally filter by category (e.g., 'case-study') and/or industry (e.g., 'technology')."""
    try:
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            task_type="retrieval_query",
            output_dimensionality=1536
        )
        if not query or query.strip() == "":
            return "Error: Search query was empty."
        query_embedding = embeddings_model.embed_query(query)
        
        if category or industry:
            rpc_name = "match_documents_filtered"
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": 10,
                "filter_category": category,
                "filter_industry": industry
            }
        else:
            rpc_name = "match_documents"
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": 10
            }
            
        rpc_response = shared_db.client.rpc(rpc_name, params).execute()
        results = rpc_response.data
        if not results:
            return "No relevant information found in the knowledge base."
            
        formatted_results = []
        for r in results:
            meta = r.get("metadata", {})
            source = meta.get("source", "Unknown")
            source_type = meta.get("type", "unknown")
            formatted_results.append({
                "id": r.get("id"),
                "content": r.get("content"),
                "source": source,
                "source_type": source_type,
                "url": meta.get("url", None),
                "metadata": meta
            })
        return json.dumps(formatted_results)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"

def call_model(state: AgentState):
    messages = state['messages']
    new_logs = ["Model call started."]
    has_system = any(isinstance(m, SystemMessage) for m in messages)
    processed_messages = []
    
    if not has_system:
        try:
            response = shared_db.client.table("knowledge_manifest").select("category, industry").execute()
            categories = set()
            industries = set()
            for row in response.data:
                if row.get("category") and row.get("category") != "general":
                    categories.add(row["category"])
                if row.get("industry") and row.get("industry") != "general":
                    industries.add(row["industry"])
            
            cats_list = list(categories)
            inds_list = list(industries)
            dynamic_context = f"\n\n--- AVAILABLE IN KNOWLEDGE BASE ---\nCategories: {', '.join(cats_list) if cats_list else 'None yet'}\nIndustries: {', '.join(inds_list) if inds_list else 'None yet'}\n-----------------------------------"
            processed_messages.append(SystemMessage(content=SYSTEM_PROMPT + dynamic_context))
        except Exception:
            processed_messages.append(SystemMessage(content=SYSTEM_PROMPT))
            
    for msg in messages:
        new_msg = msg.copy()
        if not new_msg.content or str(new_msg.content).strip() == "":
            if hasattr(new_msg, "tool_calls") and new_msg.tool_calls:
                new_msg.content = "Searching..."
            else:
                new_msg.content = "."
        processed_messages.append(new_msg)
        
    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
        model_with_tools = model.bind_tools([search_knowledge_base, get_relevant_sources])
        response = model_with_tools.invoke(processed_messages)
        if not response.content or str(response.content).strip() == "":
            if not response.tool_calls:
                response.content = "."
        new_logs.append("Model response received.")
        return {"messages": [response], "logs": new_logs}
    except Exception as e:
        raise Exception(f"Model invoke failed: {str(e)}")

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode([search_knowledge_base, get_relevant_sources]))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")
app_graph = workflow.compile()

class AgentService:
    def __init__(self):
        self.supabase = shared_db

    def log_query(self, user_query: str, agent_response: str, tools_used: list, session_id: str):
        data = {
            "user_query": user_query,
            "agent_response": agent_response,
            "tools_used": tools_used,
            "session_id": session_id
        }
        self.supabase.client.table("query_logs").insert(data).execute()

    def synthesize_final_response(self, user_query: str, retrieved_sources: list, raw_agent_response: str) -> str:
        from google import genai
        from google.genai import types
        from pydantic import BaseModel, Field
        
        class SourceItem(BaseModel):
            title: str = Field(description="The formal title of the resource")
            source: str = Field(description="The URL or filename from the manifest/RAG source field")
            source_type: str = Field(description="The source_type (e.g. 'website', 'pdf')")
            summary: str = Field(description="Active, recommendation-driven 1-2 sentence description starting directly with a present-tense active verb (e.g. 'Streamlines ERP deployment...'). Do NOT start with passive phrases.")

        class StructuredResponse(BaseModel):
            is_list_query: bool = Field(description="True if the user is asking to list, inventory, or show available documents/resources. False if they are asking an informational/content question.")
            general_answer: Optional[str] = Field(None, description="Conversational explanation in Markdown using retrieved chunks. Focus strictly on answering the question. Keep it clean.")
            case_studies: List[SourceItem] = Field(default=[], description="List of all relevant files, PDFs, one-sheets, reports, documents, case studies, or slide decks retrieved from the tools")
            blogs: List[SourceItem] = Field(default=[], description="List of all relevant web links, blogs, articles, online posts, or other website resources retrieved from the tools")

        seen = set()
        unique_sources = []
        for src in retrieved_sources:
            key = (src.get("title") or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique_sources.append(src)

        context = {
            "user_query": user_query,
            "retrieved_sources": unique_sources,
            "raw_agent_reasoning": raw_agent_response
        }

        prompt = f"""You are a professional response synthesizer for an enterprise knowledge assistant.
        Analyze the user's query, the retrieved documents, and the raw agent reasoning, and populate the response schema.

        CRITICAL ANTI-HALLUCINATION RULE:
        You MUST ONLY include items in your `case_studies` or `blogs` lists if they are present in the `retrieved_sources` JSON array. DO NOT invent, guess, or hallucinate files, titles, or documents that are not in the `retrieved_sources` array. Map all files, PDFs, one-sheets, and offline documents to the `case_studies` list. Map all website URLs and online articles to the `blogs` list. If no matching sources exist in `retrieved_sources`, leave the lists empty.

        Strictly enforce that all SourceItem summaries are in the active voice and start with a present-tense active verb.

        Context:
        {json.dumps(context, indent=2)}
        """
        try:
            client = genai.Client()
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StructuredResponse,
                    temperature=0.0
                ),
            )
            result = json.loads(response.text)
            is_list_query = result.get("is_list_query", False)
            general_answer = result.get("general_answer")
            case_studies = result.get("case_studies", [])
            blogs = result.get("blogs", [])
            
            markdown_parts = []
            if not is_list_query and general_answer:
                markdown_parts.append(general_answer.strip())
                all_sources = case_studies + blogs
                if all_sources:
                    markdown_parts.append("\n📎 You can view or download the reference materials below — perfect for reviewing or attaching to an email.\n")
                    for item in all_sources:
                        src = item.get("source", "")
                        src_type = item.get("source_type", "")
                        title = item.get("title", "")
                        if src_type in ["website", "aspx"] or src.startswith("http"):
                            markdown_parts.append(f"[{title}]({src})")
                        else:
                            markdown_parts.append(f"[DOWNLOAD:{src}]")
            else:
                markdown_parts.append("Here are the resources I found in our knowledge base:\n")
                if case_studies:
                    markdown_parts.append("### Relevant Documents\n")
                    for cs in case_studies:
                        title = cs.get("title", "")
                        src = cs.get("source", "")
                        src_type = cs.get("source_type", "")
                        summary = cs.get("summary", "").strip()
                        if src_type in ["website", "aspx"] or src.startswith("http"):
                            markdown_parts.append(f"- [{title}]({src}): {summary}")
                        else:
                            markdown_parts.append(f"- **{title}:** {summary} [DOWNLOAD:{src}]")
                    markdown_parts.append("")
                if blogs:
                    markdown_parts.append("### Additional References & Files\n")
                    for blog in blogs:
                        title = blog.get("title", "")
                        src = blog.get("source", "")
                        src_type = blog.get("source_type", "")
                        summary = blog.get("summary", "").strip()
                        if src_type in ["website", "aspx"] or src.startswith("http"):
                            markdown_parts.append(f"- [{title}]({src}): {summary}")
                        else:
                            markdown_parts.append(f"- **{title}:** {summary} [DOWNLOAD:{src}]")
                    markdown_parts.append("")
                markdown_parts.append("📎 You can view or download the reference materials below — perfect for reviewing or attaching to an email.")
            return "\n".join(markdown_parts)
        except Exception:
            return raw_agent_response

    def prompt_agent(self, request: AgentPromptRequest) -> AgentPromptResponse:
        trigger = request.prompt.strip().lower()
        if trigger in ["go orange", "go orange!"]:
            return AgentPromptResponse(
                response="🍊 **Vaco Corporate Orange Theme Engaged!** Love what you do, where you do it!",
                steps=[{"type": "status", "content": "Theme swapped!"}],
                special_event="go_orange"
            )
        if trigger in ["go blue", "go blue!", "go navy", "go navy!"]:
            return AgentPromptResponse(
                response="🔵 **Vaco Navy Theme Restored!** Ready to serve.",
                steps=[{"type": "status", "content": "Theme swapped!"}],
                special_event="go_navy"
            )

        active_prompt = SYSTEM_PROMPT
        if trigger.startswith("/pitch") or "pitch" in trigger:
            active_prompt = PITCH_SYSTEM_PROMPT
        elif trigger == "vaco!":
            active_prompt = VACO_VALUES_PROMPT

        try:
            response = self.supabase.client.table("knowledge_manifest").select("category, industry").execute()
            categories = set()
            industries = set()
            for row in response.data:
                if row.get("category") and row.get("category") != "general":
                    categories.add(row["category"])
                if row.get("industry") and row.get("industry") != "general":
                    industries.add(row["industry"])
            
            cats_list = list(categories)
            inds_list = list(industries)
            dynamic_context = f"\n\n--- AVAILABLE IN KNOWLEDGE BASE ---\nCategories: {', '.join(cats_list) if cats_list else 'None yet'}\nIndustries: {', '.join(inds_list) if inds_list else 'None yet'}\n-----------------------------------"
            full_prompt = active_prompt + dynamic_context
        except Exception:
            full_prompt = active_prompt

        initial_state = {
            "messages": [
                SystemMessage(content=full_prompt),
                HumanMessage(content=request.prompt)
            ],
            "logs": [f"Session {request.session_id} started."]
        }

        final_response = ""
        steps = []
        retrieved_docs = []

        try:
            for event in app_graph.stream(initial_state):
                for node_name, output in event.items():
                    steps.append({"type": "status", "content": f"Node '{node_name}' finished."})
                    if "logs" in output:
                        for log in output["logs"]:
                            steps.append({"type": "log", "content": log})
                    if node_name == "agent":
                        message = output["messages"][-1]
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tc in message.tool_calls:
                                steps.append({"type": "tool_call", "content": f"Tool Call Request: {tc['name']}"})
                        else:
                            final_response = message.content
                    if node_name == "tools":
                        for msg in output["messages"]:
                            try:
                                chunks = json.loads(msg.content)
                                if isinstance(chunks, list):
                                    for chunk in chunks:
                                        title = chunk.get("title") or chunk.get("metadata", {}).get("title")
                                        src = chunk.get("source") or chunk.get("metadata", {}).get("source")
                                        src_type = chunk.get("source_type") or chunk.get("metadata", {}).get("type")
                                        summary = chunk.get("summary") or chunk.get("metadata", {}).get("summary") or ""
                                        if src:
                                            retrieved_docs.append({
                                                "title": title or src,
                                                "source": src,
                                                "source_type": src_type or "unknown",
                                                "summary": summary
                                            })
                                    for i, chunk in enumerate(chunks):
                                        source = chunk.get("metadata", {}).get("source") or chunk.get("source", "Unknown")
                                        steps.append({
                                            "type": "chunk",
                                            "index": i+1,
                                            "id": chunk.get('id'),
                                            "source": source,
                                            "content": chunk.get("content", "")
                                        })
                            except Exception:
                                pass
        except Exception as e:
            steps.append({"type": "error", "content": str(e)})
            final_response = f"I encountered an error: {str(e)}"

        if retrieved_docs:
            final_response = self.synthesize_final_response(request.prompt, retrieved_docs, final_response)

        tools_used = [s["content"] for s in steps if s["type"] == "tool_call"]
        self.log_query(request.prompt, final_response, tools_used, request.session_id)
        
        special_event = "vaco_values" if trigger == "vaco!" else None
        return AgentPromptResponse(
            response=final_response,
            steps=steps,
            special_event=special_event
        )
