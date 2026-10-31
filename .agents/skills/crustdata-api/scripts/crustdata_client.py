"""
Crustdata API Client Library (Python)
API Version: 2025-11-01

A production-ready client for the Crustdata B2B Intelligence platform.
Handles authentication, versioning, credit tracking, operator validation, and pagination.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
import urllib.request
import urllib.error

logger = logging.getLogger("crustdata")

BASE_URL = "https://api.crustdata.com"
DEFAULT_API_VERSION = "2025-11-01"


class CrustdataError(Exception):
    """Base exception for Crustdata API errors."""
    def __init__(self, status_code: int, message: str, response_body: Any = None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.response_body = response_body


class CrustdataClient:
    """
    Client for Crustdata API (2025-11-01).

    Usage:
        client = CrustdataClient(api_key="your_api_key")
        credits = client.get_credits()
        print("Remaining credits:", credits["credit_balance"])
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL, api_version: str = DEFAULT_API_VERSION):
        self.api_key = api_key or os.environ.get("CRUSTDATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Crustdata API key must be provided either as argument or via CRUSTDATA_API_KEY environment variable."
            )
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.total_credits_used = 0.0

    # --------------------------------------------------------------------------
    # Internal HTTP Request Handler
    # --------------------------------------------------------------------------

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            from urllib.parse import urlencode
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urlencode(clean_params)}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-version": self.api_version,
            "Content-Type": "application/json",
            "User-Agent": "Crustdata-Python-SDK/1.0",
        }

        data_bytes = None
        if payload is not None:
            # Validate filter operators before sending
            self._validate_filter_conditions(payload)
            data_bytes = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                # Track credits if header present
                credits_header = resp.headers.get("X-Credits-Used")
                if credits_header:
                    try:
                        used = float(credits_header)
                        self.total_credits_used += used
                    except ValueError:
                        pass

                raw_body = resp.read().decode("utf-8")
                if not raw_body:
                    return None
                return json.loads(raw_body)

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("description") or err_json.get("error") or err_json.get("reason") or err_body
            except Exception:
                msg = err_body
            raise CrustdataError(e.code, msg, err_body)
        except urllib.error.URLError as e:
            raise CrustdataError(0, f"Network error: {e.reason}")

    def _validate_filter_conditions(self, obj: Any):
        """Recursively check for common operator traps like >= and <= and auto-correct them."""
        if isinstance(obj, dict):
            if "type" in obj:
                op_type = obj["type"]
                if op_type == "<=":
                    logger.warning("Crustdata API requires '=<' instead of '<='. Auto-correcting filter.")
                    obj["type"] = "=<"
                elif op_type == ">=":
                    logger.warning("Crustdata API requires '=>' instead of '>='. Auto-correcting filter.")
                    obj["type"] = "=>"
                elif op_type in ("is_null", "is_not_null") and "value" not in obj:
                    obj["value"] = None
            for v in obj.values():
                self._validate_filter_conditions(v)
        elif isinstance(obj, list):
            for item in obj:
                self._validate_filter_conditions(item)

    # --------------------------------------------------------------------------
    # Account & Billing APIs
    # --------------------------------------------------------------------------

    def get_credits(self) -> Dict[str, Any]:
        """Check credit balance and recurring credit grant. (Free, 0 credits)"""
        return self._request("GET", "/account/credits")

    def get_endpoints(self) -> List[Dict[str, Any]]:
        """List accessible endpoints, rate limits, and custom prices. (Free, 0 credits)"""
        return self._request("GET", "/account/endpoints")

    def get_usage_summary(self, group_by: Optional[str] = None, bucket: str = "1d") -> Dict[str, Any]:
        """Get aggregate usage breakdown. (Free, 0 credits)"""
        params = {"bucket": bucket}
        if group_by:
            params["group_by"] = group_by
        return self._request("GET", "/account/usage/summary", params=params)

    # --------------------------------------------------------------------------
    # Company APIs
    # --------------------------------------------------------------------------

    def identify_company(
        self,
        domains: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
        profile_urls: Optional[List[str]] = None,
        crustdata_company_ids: Optional[List[int]] = None,
        exact_match: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Resolve company from partial information. (Free, 0 credits)
        Supply exactly ONE identifier list (max 25 items).
        """
        body: Dict[str, Any] = {}
        if domains is not None:
            body["domains"] = domains
        elif names is not None:
            body["names"] = names
        elif profile_urls is not None:
            body["professional_network_profile_urls"] = profile_urls
        elif crustdata_company_ids is not None:
            body["crustdata_company_ids"] = crustdata_company_ids
        else:
            raise ValueError("Must provide exactly one identifier: domains, names, profile_urls, or crustdata_company_ids.")

        if exact_match is not None:
            body["exact_match"] = exact_match

        return self._request("POST", "/company/identify", payload=body)

    def enrich_company(
        self,
        domains: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
        profile_urls: Optional[List[str]] = None,
        crustdata_company_ids: Optional[List[int]] = None,
        fields: Optional[List[str]] = None,
        exact_match: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Deeply enrich company records. (2 credits base; +2 credits for technographics).
        Available fields: basic_info, headcount, funding, people, technographics,
                          hiring, web_traffic, employee_reviews, news, taxonomy.
        """
        body: Dict[str, Any] = {}
        if domains is not None:
            body["domains"] = domains
        elif names is not None:
            body["names"] = names
        elif profile_urls is not None:
            body["professional_network_profile_urls"] = profile_urls
        elif crustdata_company_ids is not None:
            body["crustdata_company_ids"] = crustdata_company_ids
        else:
            raise ValueError("Must provide exactly one identifier: domains, names, profile_urls, or crustdata_company_ids.")

        if fields:
            body["fields"] = fields
        if exact_match is not None:
            body["exact_match"] = exact_match

        return self._request("POST", "/company/enrich", payload=body)

    def search_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        search_mode: str = "hybrid",
        limit: int = 20,
        cursor: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search indexed company database with boolean filters and/or natural language query.
        Pricing: 0.03 credits per result + premium groups.
        Note: technographics fields can be filtered on, but NOT returned in search fields.
        """
        body: Dict[str, Any] = {"limit": limit}
        if filters:
            body["filters"] = filters
        if search_query:
            body["search"] = {"query": search_query, "mode": search_mode}
        if cursor:
            body["cursor"] = cursor
        if fields:
            body["fields"] = fields

        return self._request("POST", "/company/search", payload=body)

    def autocomplete_company(self, field: str, query: str = "") -> List[Dict[str, Any]]:
        """
        Typeahead autocomplete for company search fields (e.g. 'technology', 'basic_info.industries').
        (Free, 0 credits)
        """
        body = {"field": field, "query": query}
        return self._request("POST", "/company/search/autocomplete", payload=body)

    # --------------------------------------------------------------------------
    # Person APIs
    # --------------------------------------------------------------------------

    def identify_person(
        self,
        emails: Optional[List[str]] = None,
        profile_urls: Optional[List[str]] = None,
        scholar_urls: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Resolve person from profile URL, email, or scholar URL. (1 credit per match)
        """
        body: Dict[str, Any] = {}
        if emails is not None:
            body["emails"] = emails
        elif profile_urls is not None:
            body["professional_network_profile_urls"] = profile_urls
        elif scholar_urls is not None:
            body["research_profile_urls"] = scholar_urls
        else:
            raise ValueError("Must provide emails, profile_urls, or scholar_urls.")

        return self._request("POST", "/person/identify", payload=body)

    def enrich_person(
        self,
        profile_urls: List[str],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich people by profile URLs. (1 credit base)
        Available fields: basic_profile, experience, education, skills, certifications, honors, languages.
        """
        body: Dict[str, Any] = {"professional_network_profile_urls": profile_urls}
        if fields:
            body["fields"] = fields
        return self._request("POST", "/person/enrich", payload=body)

    def enrich_contact(
        self,
        profile_urls: Optional[List[str]] = None,
        business_emails: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        verified: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Enrich contact data (emails, phone numbers). (Enterprise accounts)
        """
        body: Dict[str, Any] = {}
        if profile_urls:
            body["professional_network_profile_urls"] = profile_urls
        elif business_emails:
            body["business_emails"] = business_emails
        else:
            raise ValueError("Must provide profile_urls or business_emails.")

        if fields:
            body["fields"] = fields
        if verified:
            body["verified"] = True

        return self._request("POST", "/person/contact/enrich", payload=body)

    def search_people(
        self,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        search_mode: str = "hybrid",
        limit: int = 20,
        cursor: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search people with structured filters and/or natural language query.
        Includes Job Title Normalization (basic_profile.normalized_title).
        """
        body: Dict[str, Any] = {"limit": limit}
        if filters:
            body["filters"] = filters
        if search_query:
            body["search"] = {"query": search_query, "mode": search_mode}
        if cursor:
            body["cursor"] = cursor
        if fields:
            body["fields"] = fields

        return self._request("POST", "/person/search", payload=body)

    def autocomplete_person(self, field: str, query: str = "") -> List[Dict[str, Any]]:
        """Autocomplete values for person search fields. (Free, 0 credits)"""
        body = {"field": field, "query": query}
        return self._request("POST", "/person/search/autocomplete", payload=body)

    # --------------------------------------------------------------------------
    # Job Postings APIs
    # --------------------------------------------------------------------------

    def search_jobs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
        sorts: Optional[List[Dict[str, str]]] = None,
        fields: Optional[List[str]] = None,
        aggregations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search indexed job postings with filters, postings technographics, and aggregations.
        Cost: 0.03 credits per result.
        """
        body: Dict[str, Any] = {"limit": limit}
        if filters:
            body["filters"] = filters
        if cursor:
            body["cursor"] = cursor
        if sorts:
            body["sorts"] = sorts
        if fields:
            body["fields"] = fields
        if aggregations:
            body["aggregations"] = aggregations

        return self._request("POST", "/job/search", payload=body)

    def autocomplete_jobs(self, field: str, query: str = "") -> List[Dict[str, Any]]:
        """Autocomplete values for job search fields (e.g. 'title', 'technology'). (Free, 0 credits)"""
        body = {"field": field, "query": query}
        return self._request("POST", "/job/search/autocomplete", payload=body)

    # --------------------------------------------------------------------------
    # Web Search & Web Fetch APIs
    # --------------------------------------------------------------------------

    def web_search(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search live web across web, news, scholar, and social. (1 credit per query)
        """
        body: Dict[str, Any] = {"query": query, "limit": limit}
        if sources:
            body["sources"] = sources
        return self._request("POST", "/web/search/live", payload=body)

    def web_fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch HTML content and title of up to 10 URLs. (1 credit per URL)
        """
        body = {"urls": urls}
        return self._request("POST", "/web/enrich/live", payload=body)
