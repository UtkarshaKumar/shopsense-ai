"""
ReAct Agent — Reasoning + Acting Loop

Implements Thought → Action → Observation → Final Answer.

Provider priority (first key found wins):
  1. Moonshot Kimi  — MOONSHOT_API_KEY set in .env
  2. Anthropic Claude — ANTHROPIC_API_KEY set in .env
  3. Demo mode       — intelligent rule-based fallback, no API required
"""
import os
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from src.data.product_catalog import ProductCatalog
from src.data.solution_cart import SolutionCart
from src.data.models import Product
from src.agent.tools import ToolRegistry


@dataclass
class ReActStep:
    """One cycle of Thought → Action → Observation"""
    thought: str
    action: str = ""
    action_params: Dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    products_found: List = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "thought": self.thought,
            "action": self.action,
            "action_params": self.action_params,
            "observation": self.observation,
            "products_found": [p.sku for p in self.products_found if hasattr(p, "sku")],
        }


@dataclass
class ReActResult:
    """Full result of a ReAct agent run"""
    steps: List[ReActStep]
    final_answer: str
    products: List[Product]
    category_context: str = "all"
    # Generative panel copy — set per-query, not from a static dict
    hero_headline: str = "Find your perfect camera,\nintelligently matched."
    hero_subtitle: str = "AI-Powered Recommendations"
    # Layout hint for the right panel
    layout_type: str = "grid"   # "grid" | "compare" | "bundle"
    success: bool = True
    # If LLM was unavailable and we fell back to demo, this explains why
    llm_error: str = ""
    # Which mode was actually used: "moonshot" | "anthropic" | "demo"
    mode_used: str = "demo"


class ReActAgent:
    """
    ReAct (Reasoning + Acting) agent for B2B commerce product discovery.

    Provider priority:
      1. Moonshot Kimi  (MOONSHOT_API_KEY)  — OpenAI-compatible, kimi-k2 default
      2. Anthropic Claude (ANTHROPIC_API_KEY) — native tool_use
      3. Demo mode                            — rule-based, no API needed
    """

    MAX_STEPS = 4

    # ── Anthropic tool schema ──────────────────────────────────────────────────
    TOOLS_ANTHROPIC = [
        {
            "name": "search_products",
            "description": "Search the product catalog by keyword query and optional category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "category": {
                        "type": "string",
                        "enum": ["cameras", "video", "accessories", "films"],
                        "description": "Optional category filter",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_product_details",
            "description": "Get full specifications for a specific product by name or SKU",
            "input_schema": {
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Product name (e.g. 'Canon EOS 450D') or SKU (e.g. 'CANON-EOS450D')",
                    }
                },
                "required": ["identifier"],
            },
        },
        {
            "name": "get_category_products",
            "description": "Get all products in a given category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["cameras", "video", "accessories", "films"],
                    }
                },
                "required": ["category"],
            },
        },
    ]

    # ── OpenAI-compatible tool schema (used by Moonshot Kimi) ──────────────────
    TOOLS_OPENAI = [
        {
            "type": "function",
            "function": {
                "name": "search_products",
                "description": "Search the product catalog by keyword query and optional category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query"},
                        "category": {
                            "type": "string",
                            "enum": ["cameras", "video", "accessories", "films"],
                            "description": "Optional category filter",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_product_details",
                "description": "Get full specifications for a specific product by name or SKU",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "Product name (e.g. 'Canon EOS 450D') or SKU code (e.g. 'CANON-EOS450D')",
                        }
                    },
                    "required": ["identifier"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_category_products",
                "description": "Get all products in a given category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["cameras", "video", "accessories", "films"],
                        }
                    },
                    "required": ["category"],
                },
            },
        },
    ]

    # Keep TOOLS as alias for backward compat
    TOOLS = TOOLS_ANTHROPIC

    def __init__(self, catalog: ProductCatalog, solution: SolutionCart):
        self.catalog = catalog
        self.solution = solution
        self.tools = ToolRegistry(catalog, solution)
        self._client = None       # Anthropic client
        self._oai_client = None   # OpenAI-compatible client (Moonshot)
        self._provider = "demo"

        def _valid_key(k: str) -> bool:
            """Return True only if key looks like a real API credential."""
            k = k.strip()
            return bool(k) and not k.startswith("#") and len(k) > 10

        # ── 1. Moonshot Kimi (primary) — initialise client if key present ──────
        moonshot_key = os.getenv("MOONSHOT_API_KEY", "").strip()
        if _valid_key(moonshot_key):
            try:
                from openai import OpenAI
                base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
                self._oai_client = OpenAI(api_key=moonshot_key, base_url=base_url)
                self._oai_model = os.getenv("MOONSHOT_MODEL", "kimi-k2")
                self._provider = "moonshot"
            except Exception:
                pass

        # ── 2. Anthropic Claude — ALWAYS initialise if key present ─────────────
        # (used as runtime fallback when Moonshot fails, independent of priority)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if _valid_key(anthropic_key):
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=anthropic_key)
                self._anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
                # Only set provider to anthropic if moonshot wasn't found
                if self._provider == "demo":
                    self._provider = "anthropic"
            except Exception:
                pass

    @property
    def has_llm(self) -> bool:
        return self._provider != "demo"

    def run(self, query: str, history: List[Dict] = None) -> ReActResult:
        llm_err = ""

        # ── Try Moonshot first ───────────────────────────────────────────────
        if self._provider == "moonshot":
            try:
                result = self._run_with_openai(query, history or [])
                result.mode_used = "moonshot"
                return result
            except Exception as e:
                err = str(e)
                if "balance" in err.lower() or "quota" in err.lower() or "402" in err or "insufficient" in err.lower():
                    llm_err = "⚠️ Moonshot billing: insufficient credits. Top up at platform.moonshot.cn."
                elif "401" in err or "authentication" in err.lower() or "api key" in err.lower():
                    llm_err = "⚠️ Moonshot API key is invalid (401). Update MOONSHOT_API_KEY in .env."
                else:
                    llm_err = f"⚠️ Moonshot error: {err[:120]}"
                # Cascade → try Anthropic if client was initialised
                if self._client is not None:
                    try:
                        result = self._run_with_llm(query, history or [])
                        result.mode_used = "anthropic"
                        result.llm_error = llm_err  # surface moonshot warning but mark as anthropic
                        return result
                    except Exception:
                        pass  # fall through to demo

        # ── Try Anthropic directly when it is the primary provider ──────────
        elif self._provider == "anthropic":
            try:
                result = self._run_with_llm(query, history or [])
                result.mode_used = "anthropic"
                return result
            except Exception as e:
                err = str(e)
                if "credit balance" in err or "billing" in err.lower() or "402" in err:
                    llm_err = "⚠️ Anthropic billing: credit balance too low. Add credits at console.anthropic.com."
                elif "401" in err or "authentication" in err.lower() or "invalid x-api-key" in err.lower():
                    llm_err = "⚠️ Anthropic API key invalid (401). Update ANTHROPIC_API_KEY in .env."
                else:
                    llm_err = f"⚠️ Anthropic error: {err[:120]}"
                # Fall through to demo mode

        result = self._run_demo(query)
        result.mode_used = "demo"
        result.llm_error = llm_err
        return result

    # ── LLM-powered mode ──────────────────────────────────────────────────────

    def _build_system(self) -> str:
        products = self.catalog.get_all()
        lines = [
            "You are an expert consumer electronics advisor for ShopSense AI — an online camera and electronics store.",
            "Your catalog contains ONLY: Cameras (DSLR & compact), Camcorders & Video, Camera Accessories (bags, lenses, tripods, memory cards), and Films & Media.",
            "You ONLY handle queries about photography, cameras, video and related accessories.",
            "",
            "SCOPE RULE: If a query is clearly unrelated to cameras or consumer electronics photography (e.g. cars, food, travel, industrial equipment, home appliances), politely decline and explain what you do offer. Do NOT search the catalog.",
            "",
            "PRODUCT CATALOG:",
        ]
        for p in products:
            specs = [f"{k}={v}" for k, v in list(p.specifications.items())[:3]]
            line = f"  • {p.name} [{p.sku}] {p.category.value} ${p.price:,.0f} — {p.description}"
            if specs:
                line += f" | {', '.join(specs)}"
            lines.append(line)
        lines += [
            "",
            "INSTRUCTIONS:",
            "- Always call at least one tool before giving your final answer (unless out of scope)",
            "- Recommend complete setups: camera + memory card + bag + accessories where relevant",
            "- Use exact product names and SKUs in your responses",
            "- When comparing products, highlight key spec differences clearly",
            "- After tools, give a clear concise recommendation",
        ]
        return "\n".join(lines)

    def _run_with_llm(self, query: str, history: List[Dict]) -> ReActResult:
        system = self._build_system()
        messages = []
        for msg in history[-6:]:
            role = "assistant" if msg["role"] == "assistant" else "user"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        steps: List[ReActStep] = []
        all_products: List[Product] = []
        category_context = "all"

        for _ in range(self.MAX_STEPS):
            resp = self._client.messages.create(
                model=self._anthropic_model,
                max_tokens=2048,
                system=system,
                tools=self.TOOLS,
                messages=messages,
            )

            thought = ""
            tool_uses = []
            for block in resp.content:
                if block.type == "text":
                    thought = block.text.strip()
                elif block.type == "tool_use":
                    tool_uses.append(block)

            if not tool_uses or resp.stop_reason == "end_turn":
                steps.append(ReActStep(thought=thought or "Here is my final recommendation.", action="respond"))
                deduped = self._dedup(all_products)
                q_lower = query.lower()
                is_cmp = any(w in q_lower for w in ["compare", "vs", "versus"])
                is_bndl = any(w in q_lower for w in ["bundle", "complete", "full", "everything", "starter kit", "setup", "build"])
                space_m = re.search(r"(\d[\d,]*)\s*(?:sq\s*ft|sqft|square\s*feet?)", q_lower)
                space_v = int(space_m.group(1).replace(",", "")) if space_m else None
                cat = self._dominant_cat(deduped, "all") if deduped else None
                headline, subtitle, layout = self._generate_panel_copy(
                    query, cat if cat != "all" else None, space_v, is_cmp, is_bndl, deduped
                )
                return ReActResult(
                    steps=steps,
                    final_answer=thought or "Here are the products that match your requirements.",
                    products=deduped,
                    category_context=category_context,
                    hero_headline=headline,
                    hero_subtitle=subtitle,
                    layout_type=layout,
                )

            tool_results = []
            for tu in tool_uses:
                result = self.tools.execute(tu.name, tu.input)
                prods: List[Product] = []
                if result.data:
                    if isinstance(result.data, list):
                        prods = [p for p in result.data if hasattr(p, "sku")]
                    elif hasattr(result.data, "sku"):
                        prods = [result.data]
                all_products.extend(prods)
                if prods:
                    category_context = self._dominant_cat(prods, category_context)

                if prods:
                    obs = f"{result.message}: " + ", ".join(f"{p.name} (${p.price:,.0f})" for p in prods[:3])
                else:
                    obs = result.message if result.success else f"Error: {result.error}"

                steps.append(ReActStep(
                    thought=thought,
                    action=tu.name,
                    action_params=dict(tu.input),
                    observation=obs,
                    products_found=prods[:3],
                ))
                thought = ""  # Only show thought on first tool of the turn

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": obs,
                })

            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": tool_results})

        # Final answer pass
        messages.append({"role": "user", "content": "Give your final recommendation now. Be specific."})
        final_resp = self._client.messages.create(
            model=self._anthropic_model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        final_text = ""
        for block in final_resp.content:
            if hasattr(block, "text"):
                final_text = block.text.strip()
                break

        deduped = self._dedup(all_products)
        q_lower = query.lower()
        is_cmp = any(w in q_lower for w in ["compare", "vs", "versus"])
        is_bndl = any(w in q_lower for w in ["bundle", "complete", "full", "everything", "starter kit", "setup", "build"])

        # ── LLM-generated panel copy (headline, subtitle, layout) ──────────────
        headline, subtitle, layout = self._get_llm_panel_copy(query, deduped, is_cmp, is_bndl)

        return ReActResult(
            steps=steps,
            final_answer=final_text or "Here are the products I found for you.",
            products=deduped,
            category_context=category_context,
            hero_headline=headline,
            hero_subtitle=subtitle,
            layout_type=layout,
        )

    # ── OpenAI-compatible mode (Moonshot Kimi) ────────────────────────────────

    def _run_with_openai(self, query: str, history: List[Dict]) -> ReActResult:
        """
        ReAct loop using OpenAI-compatible API — works with Moonshot Kimi and
        any other provider that supports the OpenAI chat completions + function
        calling format.
        """
        system = self._build_system()
        messages: List[Dict] = [{"role": "system", "content": system}]
        for msg in history[-6:]:
            role = "assistant" if msg["role"] == "assistant" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": query})

        steps: List[ReActStep] = []
        all_products: List[Product] = []
        category_context = "all"

        for _ in range(self.MAX_STEPS):
            resp = self._oai_client.chat.completions.create(
                model=self._oai_model,
                max_tokens=2048,
                tools=self.TOOLS_OPENAI,
                tool_choice="auto",
                messages=messages,
            )

            msg_out = resp.choices[0].message
            thought = (msg_out.content or "").strip()
            tool_calls = msg_out.tool_calls or []

            if not tool_calls or resp.choices[0].finish_reason == "stop":
                steps.append(ReActStep(
                    thought=thought or "Here is my final recommendation.",
                    action="respond",
                ))
                break

            # Append assistant turn with tool calls
            messages.append(msg_out)

            tool_results_msgs = []
            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                result = self.tools.execute(fn_name, fn_args)
                prods: List[Product] = []
                if result.data:
                    if isinstance(result.data, list):
                        prods = [p for p in result.data if hasattr(p, "sku")]
                    elif hasattr(result.data, "sku"):
                        prods = [result.data]
                all_products.extend(prods)
                if prods:
                    category_context = self._dominant_cat(prods, category_context)

                obs = (
                    f"{result.message}: " + ", ".join(f"{p.name} (${p.price:,.0f})" for p in prods[:3])
                    if prods else result.message if result.success else f"Error: {result.error}"
                )

                steps.append(ReActStep(
                    thought=thought,
                    action=fn_name,
                    action_params=fn_args,
                    observation=obs,
                    products_found=prods[:3],
                ))
                thought = ""  # Only emit thought on first tool of the turn

                tool_results_msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": obs,
                })

            messages.extend(tool_results_msgs)

        # Final answer pass
        messages.append({"role": "user", "content": "Give your final recommendation now. Be specific and concise."})
        final_resp = self._oai_client.chat.completions.create(
            model=self._oai_model,
            max_tokens=1024,
            messages=messages,
        )
        final_text = (final_resp.choices[0].message.content or "").strip()

        deduped = self._dedup(all_products)
        q_lower = query.lower()
        is_cmp = any(w in q_lower for w in ["compare", "vs", "versus"])
        is_bndl = any(w in q_lower for w in ["bundle", "complete", "full", "everything", "starter kit", "setup", "build"])
        headline, subtitle, layout = self._get_llm_panel_copy_openai(query, deduped, is_cmp, is_bndl)

        return ReActResult(
            steps=steps,
            final_answer=final_text or "Here are the products I found for you.",
            products=deduped,
            category_context=category_context,
            hero_headline=headline,
            hero_subtitle=subtitle,
            layout_type=layout,
        )

    def _get_llm_panel_copy_openai(
        self,
        query: str,
        products: List[Product],
        is_compare: bool,
        is_bundle: bool,
    ) -> Tuple[str, str, str]:
        """Generate panel copy via OpenAI-compatible client (Moonshot)."""
        if not self._oai_client or not products:
            return self._generate_panel_copy(query, None, None, is_compare, is_bundle, products)

        product_lines = "\n".join(
            f"  - {p.name} ({p.category.value}, ${p.price:,.0f})" for p in products[:6]
        )
        prompt = (
            f'User query: "{query}"\n\nProducts found:\n{product_lines}\n\n'
            "Generate a product showcase panel. Rules:\n"
            "- hero_headline: 2-line punchy headline (max 8 words, \\n between lines). Be specific.\n"
            "- subtitle: Short context label (max 6 words)\n"
            "- layout: grid | compare | bundle\n\n"
            'JSON only: {"hero_headline":"...","subtitle":"...","layout":"..."}'
        )
        try:
            resp = self._oai_client.chat.completions.create(
                model=self._oai_model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = (resp.choices[0].message.content or "").strip()
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                data = json.loads(m.group())
                headline = data.get("hero_headline", "").replace("\\n", "\n")
                subtitle = data.get("subtitle", "")
                layout = data.get("layout", "grid")
                if layout not in ("grid", "compare", "bundle"):
                    layout = "grid"
                if headline and subtitle:
                    return headline, subtitle, layout
        except Exception:
            pass

        q_lower = query.lower()
        space_m = re.search(r"(\d[\d,]*)\s*(?:sq\s*ft|sqft|square\s*feet?)", q_lower)
        space_v = int(space_m.group(1).replace(",", "")) if space_m else None
        cat = self._dominant_cat(products, "all") if products else None
        return self._generate_panel_copy(query, cat if cat != "all" else None, space_v, is_compare, is_bundle, products)

    # ── Demo mode ─────────────────────────────────────────────────────────────

    # Signals that indicate a query is about consumer electronics / photography
    _INFRA_SIGNALS = [
        "camera", "dslr", "mirrorless", "compact", "point and shoot", "slr",
        "canon", "nikon", "sony", "fuji", "fujifilm", "kodak",
        "photo", "photograph", "shoot", "shooting", "picture", "image",
        "video", "camcorder", "record", "recording", "handycam", "legria",
        "hd", "fullhd", "1080p", "4k",
        "lens", "tripod", "bag", "camera bag", "sd card", "memory card", "sdhc",
        "film", "colour film", "color film", "analogue", "iso", "35mm",
        "starter kit", "studio", "action cam",
    ]

    # Signals that clearly indicate an out-of-scope request
    _OOT_SIGNALS = [
        "home theatre", "home theater", "cinema", "movie", "soundbar",
        "television", "smart tv", "projector", "amplifier", "speaker",
        "car", "vehicle", "bike", "motorcycle",
        "food", "restaurant", "recipe", "cooking",
        "travel", "hotel", "flight", "vacation", "holiday",
        "fashion", "clothing", "shoes", "apparel",
        "gaming console", "playstation", "xbox", "nintendo",
        "smartphone", "mobile phone", "iphone", "android",
        "furniture", "bedroom", "kitchen", "garden", "home decor",
        "hair", "beauty", "cosmetic", "makeup",
    ]

    @staticmethod
    def _kw_match(keyword: str, text: str) -> bool:
        """
        Match a keyword against text with a word boundary at the START only.

        This means:
        - "heat"  matches "heat"  but NOT "theatre"  (no boundary before 'h' in 'theat|r|e')
        - "cool"  matches "cool" and "cooling" but NOT "schooling"
        - "distribut" matches "distribution" prefix-style
        """
        return bool(re.search(r"\b" + re.escape(keyword), text))

    def _is_out_of_scope(self, q: str) -> bool:
        """Return True if the query is clearly unrelated to cameras / consumer electronics."""
        has_infra = any(self._kw_match(kw, q) for kw in self._INFRA_SIGNALS)
        if has_infra:
            return False
        has_oot = any(kw in q for kw in self._OOT_SIGNALS)
        return has_oot

    def _run_demo(self, query: str) -> ReActResult:
        """
        Intelligent demo mode — real catalog tool calls, realistic ReAct reasoning.
        Looks indistinguishable from a real LLM-driven loop.
        """
        q = query.lower()
        steps: List[ReActStep] = []
        all_products: List[Product] = []
        category_context = "all"

        # ── Out-of-scope guard ─────────────────────────────────────────────────
        if self._is_out_of_scope(q):
            steps.append(ReActStep(
                thought=(
                    f"The query \"{query}\" does not relate to cameras or consumer electronics photography. "
                    "Our catalog covers: Cameras (DSLR & compact), Camcorders & Video, "
                    "Camera Accessories, and Films & Media."
                ),
                action="respond",
                action_params={},
                observation="Query is outside the product catalog scope — returning helpful redirect.",
            ))
            return ReActResult(
                steps=steps,
                final_answer=(
                    f"I specialise in **cameras and consumer electronics** — "
                    f"I wasn't able to find anything in our catalog for *\"{query}\"*.\n\n"
                    "Here's what I can help you with:\n"
                    "• 📷 **Cameras** — DSLR, compact, mirrorless (Canon, Nikon, Sony, Fujifilm)\n"
                    "• 🎥 **Video** — Camcorders, HD video cameras (Sony, Canon)\n"
                    "• 🎒 **Accessories** — Bags, lenses, tripods, memory cards\n"
                    "• 🎞 **Films & Media** — Colour film, Kodak, Fujifilm\n\n"
                    "Try asking something like: *\"Best camera for beginners\"* "
                    "or *\"Compare Canon vs Sony compact cameras.\"*"
                ),
                products=[],
                category_context="all",
                hero_headline="Every shot starts\nwith the right camera.",
                hero_subtitle="ShopSense AI · Consumer Electronics",
                layout_type="grid",
                success=False,
            )

        # ── Detect intent ──────────────────────────────────────────────────────
        # Keywords use word-boundary matching to prevent false positives
        cat_map = {
            "cameras": ["camera", "dslr", "mirrorless", "compact", "slr", "eos", "ixus", "finepix", "cyber-shot", "cybershot", "photograph", "shoot"],
            "video": ["video", "camcorder", "handycam", "legria", "record", "hd cam", "fullhd", "1080p", "4k"],
            "accessories": ["bag", "lens", "tripod", "sd card", "memory card", "sdhc", "gorilla", "prime", "ef lens"],
            "films": ["film", "colour film", "color film", "kodak", "fuji film", "superia", "35mm", "analogue", "iso 400", "iso 200"],
        }
        detected_cat: Optional[str] = None
        for cat, kws in cat_map.items():
            if any(self._kw_match(kw, q) for kw in kws):
                detected_cat = cat
                break

        space_match = re.search(r"(\d[\d,]*)\s*(?:sq\s*ft|sqft|square\s*feet?)", q)
        space_req = int(space_match.group(1).replace(",", "")) if space_match else None

        is_compare = any(w in q for w in ["compare", "vs", "versus", "difference", "between"])
        is_bundle = any(w in q for w in ["bundle", "complete", "full", "everything", "build", "all-in", "starter kit", "setup"])

        # ── Step 1: Search / browse ────────────────────────────────────────────
        if detected_cat:
            thought = f"The customer needs {detected_cat} products"
            thought += f". I'll search our {detected_cat} catalog for products that match their requirements."

            res = self.tools.execute("search_products", {"query": query, "category": detected_cat})
            prods = [p for p in (res.data or []) if hasattr(p, "sku")]

            # Rank by space fit
            if space_req and prods:
                fits = [p for p in prods if p.specifications.get("capacity_sqft", 0) >= space_req * 0.75]
                if fits:
                    prods = sorted(fits, key=lambda p: abs(p.specifications.get("capacity_sqft", 9999) - space_req))

            obs = f"Found {len(prods)} {detected_cat} products"
            if space_req:
                obs += f" suitable for {space_req:,} sq ft"
            if prods:
                obs += ": " + ", ".join(f"{p.name} ({p.specifications.get('capacity_sqft', 'N/A')} sq ft)" for p in prods[:2] if p.specifications.get("capacity_sqft"))

            steps.append(ReActStep(
                thought=thought,
                action="search_products",
                action_params={"query": query, "category": detected_cat},
                observation=obs,
                products_found=prods[:3],
            ))
            all_products.extend(prods)
            category_context = detected_cat

        elif is_compare:
            thought = "The customer wants to compare specific products. I'll search for each model separately to find the exact ones."
            # Split on "vs" to find each product independently
            vs_parts = re.split(r'\bvs\.?\b|\bversus\b|\bor\b', q, maxsplit=1)
            compare_prods = []
            for part in vs_parts[:2]:
                # Strip common words: "compare", "and", "between"
                clean = re.sub(r'\b(compare|between|and|the)\b', '', part.strip()).strip()
                if clean:
                    res = self.tools.execute("search_products", {"query": clean})
                    found = [p for p in (res.data or []) if hasattr(p, "sku")]
                    if found:
                        compare_prods.append(found[0])
            # Fallback to general search if splitting didn't work
            if len(compare_prods) < 2:
                res = self.tools.execute("search_products", {"query": query})
                compare_prods = [p for p in (res.data or []) if hasattr(p, "sku")][:4]

            steps.append(ReActStep(
                thought=thought,
                action="search_products",
                action_params={"query": query},
                observation=f"Found {len(compare_prods)} products for comparison: "
                            + ", ".join(p.name for p in compare_prods[:4]),
                products_found=compare_prods[:4],
            ))
            all_products.extend(compare_prods)

        else:
            # No strong category signal — check for any electronics/camera signals
            # before running a broad search.
            infra_signals_in_q = any(kw in q for kw in self._INFRA_SIGNALS)
            if not infra_signals_in_q:
                # Ambiguous query — ask for clarification
                steps.append(ReActStep(
                    thought=(
                        f"The query \"{query}\" doesn't clearly map to any product category. "
                        "I need more details to make a useful recommendation."
                    ),
                    action="respond",
                    action_params={},
                    observation="Insufficient context to search catalog — requesting clarification.",
                ))
                return ReActResult(
                    steps=steps,
                    final_answer=(
                        f"I'd love to help, but I need a bit more context.\n\n"
                        "I specialise in **cameras and consumer electronics**:\n"
                        "• 📷 Cameras — DSLR, compact, mirrorless\n"
                        "• 🎥 Video — Camcorders, HD cameras\n"
                        "• 🎒 Accessories — Bags, lenses, tripods, cards\n"
                        "• 🎞 Films & Media — Colour film, SD cards\n\n"
                        "Could you tell me more about what you're looking for? For example:\n"
                        "- Are you looking for a DSLR, compact, or action camera?\n"
                        "- What's your budget range?\n"
                        "- Are you a beginner or enthusiast photographer?"
                    ),
                    products=[],
                    category_context="all",
                    hero_headline="Tell me what\nyou're looking for.",
                    hero_subtitle="ShopSense AI · Consumer Electronics",
                    layout_type="grid",
                    success=True,
                )
            # Electronics signals present — broad search is reasonable
            thought = "The customer has a general electronics or photography requirement. Let me search the full catalog to understand what's available."
            res = self.tools.execute("search_products", {"query": query})
            prods = [p for p in (res.data or []) if hasattr(p, "sku")]
            steps.append(ReActStep(
                thought=thought,
                action="search_products",
                action_params={"query": query},
                observation=f"Found {len(prods)} matching products across all categories",
                products_found=prods[:3],
            ))
            all_products.extend(prods)

        # ── Step 2: Inspect top product ────────────────────────────────────────
        if all_products:
            top = all_products[0]
            thought = (
                f"The {top.name} looks like the strongest match. "
                f"Let me pull its full specifications to confirm it meets the requirements."
            )
            res = self.tools.execute("get_product_details", {"identifier": top.sku})
            obs = f"{top.name} is {'✓ in stock' if top.in_stock else '✗ out of stock'}, ${top.price:,.0f}"
            if space_req and top.specifications.get("capacity_sqft"):
                cap = top.specifications["capacity_sqft"]
                obs += f" — rated for {cap:,} sq ft"
                if cap >= space_req:
                    obs += " ✓ covers requirement"
                else:
                    obs += f" ⚠ under-spec'd by {space_req - cap:,} sq ft"
            steps.append(ReActStep(
                thought=thought,
                action="get_product_details",
                action_params={"identifier": top.sku},
                observation=obs,
                products_found=[top] if res.data else [],
            ))

        # ── Step 3: Complete the solution ──────────────────────────────────────
        cats_present = {p.category.value for p in all_products}
        missing_cats = {"cameras", "accessories"} - cats_present

        if is_bundle or (missing_cats and len(all_products) < 6):
            cats_to_add = list(missing_cats)[:2] if missing_cats else []
            if not cats_to_add and is_bundle:
                cats_to_add = [c for c in ["accessories", "video"] if c != detected_cat][:2]

            if cats_to_add:
                thought = (
                    "For a complete camera kit, the customer may also need "
                    + " and ".join(cats_to_add)
                    + ". Let me find the best options in those categories."
                )
                added = []
                for cat in cats_to_add:
                    res = self.tools.execute("get_category_products", {"category": cat})
                    cat_prods = [p for p in (res.data or []) if hasattr(p, "sku") and p.in_stock]
                    if cat_prods:
                        # Pick best for budget: pick mid-range
                        sorted_prods = sorted(cat_prods, key=lambda p: p.price or 0)
                        pick = sorted_prods[len(sorted_prods) // 2] if len(sorted_prods) > 1 else sorted_prods[0]
                        added.append(pick)
                        all_products.append(pick)

                if added:
                    obs = "Added " + ", ".join(f"{p.name} ({p.category.value})" for p in added) + " to complete the solution"
                    steps.append(ReActStep(
                        thought=thought,
                        action="get_category_products",
                        action_params={"category": cats_to_add[0]},
                        observation=obs,
                        products_found=added,
                    ))

        # ── Build final answer + generative panel copy ─────────────────────────
        deduped = self._dedup(all_products)
        final = self._make_demo_answer(query, deduped, detected_cat, space_req, is_compare, is_bundle)
        headline, subtitle, layout = self._generate_panel_copy(
            query, detected_cat, space_req, is_compare, is_bundle, deduped
        )

        return ReActResult(
            steps=steps,
            final_answer=final,
            products=deduped,
            category_context=category_context,
            hero_headline=headline,
            hero_subtitle=subtitle,
            layout_type=layout,
        )

    def _make_demo_answer(
        self,
        query: str,
        products: List[Product],
        cat: Optional[str],
        space: Optional[int],
        is_compare: bool,
        is_bundle: bool,
    ) -> str:
        if not products:
            return (
                "Could you share a bit more about what you're looking for?\n\n"
                "For example:\n"
                "• What type of camera — DSLR, compact, or action cam?\n"
                "• What's your budget range?\n"
                "• Are you a beginner or experienced photographer?"
            )

        top = self._dedup(products)

        # ── Comparison ────────────────────────────────────────────────────────
        if is_compare and len(top) >= 2:
            a, b = top[0], top[1]
            lines = [f"**{a.name} vs {b.name}**", ""]
            for p in [a, b]:
                lines += [
                    f"**{p.name}** — `{p.sku}` — ${p.price:,.0f}",
                    p.description,
                ]
                for k, v in list(p.specifications.items())[:3]:
                    lines.append(f"  • {k.replace('_', ' ').title()}: {v}")
                lines.append("")
            # Verdict
            if a.price and b.price:
                cheaper = a if a.price < b.price else b
                cap_a = a.specifications.get("capacity_sqft", 0)
                cap_b = b.specifications.get("capacity_sqft", 0)
                bigger = a if cap_a > cap_b else b
                lines += [
                    "**Recommendation:**",
                    f"• Best value: **{cheaper.name}** (${cheaper.price:,.0f})",
                ]
                if cap_a != cap_b:
                    lines.append(f"• Best coverage: **{bigger.name}** ({max(cap_a, cap_b):,} sq ft)")
            return "\n".join(lines)

        # ── Complete bundle ────────────────────────────────────────────────────
        if is_bundle or len({p.category.value for p in top}) >= 3:
            lines = ["**Complete Infrastructure Bundle**", ""]
            total = 0
            by_cat = {}
            for p in top:
                cv = p.category.value
                if cv not in by_cat:
                    by_cat[cv] = p
            for cv, p in by_cat.items():
                lines.append(f"**{cv.title()}** — {p.name} (`{p.sku}`) — ${p.price:,.0f}")
                lines.append(f"  {p.description}")
                lines.append("")
                total += p.price or 0
            if total:
                lines += ["---", f"**Estimated total: ${total:,.0f}**"]
            return "\n".join(lines)

        # ── Single category recommendation ────────────────────────────────────
        p = top[0]
        lines = [f"**Top Recommendation: {p.name}**", "", p.description, ""]
        for k, v in list(p.specifications.items())[:3]:
            lines.append(f"• {k.replace('_', ' ').title()}: {v}")
        lines.append("")

        if space and p.specifications.get("capacity_sqft"):
            cap = p.specifications["capacity_sqft"]
            if cap >= space:
                lines.append(f"✓ Fully covers your {space:,} sq ft (rated for {cap:,} sq ft)")
            else:
                lines.append(f"⚠ Rated for {cap:,} sq ft — consider 2× units for {space:,} sq ft")
            lines.append("")

        lines.append(f"**SKU:** `{p.sku}` · **Price:** ${p.price:,.0f} · **{'In Stock' if p.in_stock else 'Out of Stock'}**")

        if len(top) > 1:
            others = ", ".join(p2.name for p2 in top[1:3])
            lines += ["", f"Also found: {others}"]

        return "\n".join(lines)

    # ── LLM-powered generative panel copy ─────────────────────────────────────

    def _get_llm_panel_copy(
        self,
        query: str,
        products: List[Product],
        is_compare: bool,
        is_bundle: bool,
    ) -> Tuple[str, str, str]:
        """
        Ask Claude to generate contextual hero headline, subtitle, and layout hint.
        Falls back to rule-based copy if LLM call fails.
        """
        if not self._client or not products:
            return self._generate_panel_copy(query, None, None, is_compare, is_bundle, products)

        product_lines = "\n".join(
            f"  - {p.name} ({p.category.value}, ${p.price:,.0f})"
            for p in products[:6]
        )
        prompt = (
            f'User query: "{query}"\n\n'
            f"Products found:\n{product_lines}\n\n"
            "Generate a concise product showcase panel for these results.\n"
            "Rules:\n"
            "- hero_headline: 2-line punchy headline (max 8 words, use \\n between lines). "
            "Match the specific products and use case — avoid generic phrases.\n"
            "- subtitle: Short category/context label (max 6 words)\n"
            "- layout: one of [grid, compare, bundle]. Use 'compare' only if user asked to "
            "compare, 'bundle' only if user asked for a complete bundle, otherwise 'grid'.\n\n"
            'Respond with JSON only: {"hero_headline": "...", "subtitle": "...", "layout": "..."}'
        )

        try:
            resp = self._client.messages.create(
                model=self._anthropic_model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            # Extract JSON even if Claude wraps it in a code fence
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                data = json.loads(m.group())
                headline = data.get("hero_headline", "").replace("\\n", "\n")
                subtitle = data.get("subtitle", "")
                layout = data.get("layout", "grid")
                if layout not in ("grid", "compare", "bundle"):
                    layout = "grid"
                if headline and subtitle:
                    return headline, subtitle, layout
        except Exception:
            pass

        # Fallback to rule-based
        q_lower = query.lower()
        space_m = re.search(r"(\d[\d,]*)\s*(?:sq\s*ft|sqft|square\s*feet?)", q_lower)
        space_v = int(space_m.group(1).replace(",", "")) if space_m else None
        cat = self._dominant_cat(products, "all") if products else None
        return self._generate_panel_copy(query, cat if cat != "all" else None, space_v, is_compare, is_bundle, products)

    # ── Rule-based panel copy (demo mode fallback) ─────────────────────────────

    def _generate_panel_copy(
        self,
        query: str,
        category: Optional[str],
        space: Optional[int],
        is_compare: bool,
        is_bundle: bool,
        products: List[Product],
    ) -> tuple:
        """
        Generate contextual hero headline + subtitle + layout_type for the right panel.
        Everything is driven by the actual query — nothing comes from a static dict.
        """
        q = query.lower()

        if is_compare:
            # Use actual product names in the headline if we found products
            if len(products) >= 2:
                n1 = products[0].name.split()[0]
                n2 = products[1].name.split()[0]
            else:
                n1, n2 = "Option A", "Option B"
            headline = f"{n1} vs {n2}.\nMake the right call."
            subtitle = "Side-by-Side Product Comparison"
            layout = "compare"

        elif is_bundle:
            # Only show "bundle" layout when user explicitly asked for one
            headline = "The complete kit,\ncurated for you."
            subtitle = "Complete Camera & Accessories Bundle"
            layout = "bundle"

        elif category == "cameras":
            headline = "Find your perfect camera,\nintelligently matched."
            subtitle = "Cameras · DSLR, Compact & Mirrorless"
            layout = "grid"

        elif category == "video":
            headline = "Capture every moment,\nin stunning HD."
            subtitle = "Camcorders & Video Cameras"
            layout = "grid"

        elif category == "accessories":
            headline = "Complete your kit,\naccessory by accessory."
            subtitle = "Camera Accessories & Gear"
            layout = "grid"

        elif category == "films":
            headline = "The art of analogue,\nstill alive."
            subtitle = "Films & Media Collection"
            layout = "grid"

        else:
            # Generic but still responsive to the query
            if "beginner" in q or "starter" in q:
                headline = "Your first camera,\nperfectly chosen."
            elif "compare" in q or "vs" in q:
                headline = "Side by side,\nclear as daylight."
            elif "budget" in q or "under" in q or "cheap" in q:
                headline = "Great photography,\nwithout the price tag."
            else:
                headline = "Find your perfect camera,\nintelligently matched."
            subtitle = "ShopSense AI · Consumer Electronics"
            layout = "grid"

        return headline, subtitle, layout

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _dominant_cat(self, prods: List[Product], current: str) -> str:
        if not prods:
            return current
        cats = {p.category.value for p in prods}
        return list(cats)[0] if len(cats) == 1 else current

    def _dedup(self, prods: List[Product]) -> List[Product]:
        seen, out = set(), []
        for p in prods:
            if p.sku not in seen:
                seen.add(p.sku)
                out.append(p)
        return out
