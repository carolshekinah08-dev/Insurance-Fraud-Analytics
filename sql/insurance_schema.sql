--
-- PostgreSQL database dump
--

\restrict fym08szTqUlafpMofJOSnjGgcQ4PBwYep8vVRnMuSZekepckoOLLVNlog1PQGhK

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: reit_portfolio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reit_portfolio (
    "PROPERTY_ID" text,
    "INCIDENT_DATE" text,
    "MANAGER_ID" text,
    "ADJUSTER_ID" text,
    "PROPERTY_TYPE" text,
    "CURRENCY_CODE" text,
    "SQUARE_FOOTAGE" text,
    "VALUATION_LOCAL" text,
    "CURRENT_PREMIUM_LOCAL" text,
    "BASE_PREMIUM_USD" text,
    "INSURANCE_METADATA_JSON" text,
    "YEAR" text,
    "MONTH" text,
    "QUARTER" text,
    "INCIDENT_CLASSIFICATION" text,
    "PAYOUT_AUTHORIZED" text,
    "CONTRACTOR_A85" text,
    "ADJUSTER_GRATUITY" text,
    "DECODED_CONTRACTOR" text,
    "EXCHANGE_RATE_USD" text,
    "VALUATION_USD" text,
    "CURRENT_PREMIUM_USD" text,
    "PREMIUM_SPIKE_USD" text,
    "PAYOUT_TO_VALUE_RATIO" text,
    "PHANTOM_CLAIM_SUSPECT" text,
    "ADJUSTER_KICKBACK_RATIO" text,
    "TOTAL_FINANCIAL_DAMAGE_USD" text,
    "COUNTRY_CODE" text
);


--
-- Name: mv_adjuster_tracker; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_adjuster_tracker AS
 SELECT "ADJUSTER_ID" AS adjuster_id,
    sum(("ADJUSTER_GRATUITY")::numeric) AS total_bribes,
    count(DISTINCT
        CASE
            WHEN ("DECODED_CONTRACTOR" <> 'Standard_Vendor'::text) THEN "DECODED_CONTRACTOR"
            ELSE NULL::text
        END) AS unique_shell_companies,
    sum(("PAYOUT_AUTHORIZED")::numeric) AS total_authorized_payouts
   FROM public.reit_portfolio
  GROUP BY "ADJUSTER_ID"
  WITH NO DATA;


--
-- Name: mv_contractor_tracker; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_contractor_tracker AS
 SELECT "DECODED_CONTRACTOR" AS contractor,
    count(*) AS total_incidents,
    sum(("PAYOUT_AUTHORIZED")::numeric) AS total_payout_stolen,
    avg(("PREMIUM_SPIKE_USD")::numeric) AS avg_premium_spike
   FROM public.reit_portfolio
  WHERE (("DECODED_CONTRACTOR" IS NOT NULL) AND ("DECODED_CONTRACTOR" <> 'Standard_Vendor'::text))
  GROUP BY "DECODED_CONTRACTOR"
  WITH NO DATA;


--
-- Name: vw_adjuster_tracker; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_adjuster_tracker AS
 SELECT "ADJUSTER_ID" AS adjuster_id,
    sum(("ADJUSTER_GRATUITY")::numeric) AS total_bribes,
    count(DISTINCT
        CASE
            WHEN ("DECODED_CONTRACTOR" <> 'Standard_Vendor'::text) THEN "DECODED_CONTRACTOR"
            ELSE NULL::text
        END) AS unique_shell_companies,
    sum(("PAYOUT_AUTHORIZED")::numeric) AS total_authorized_payouts
   FROM public.reit_portfolio
  GROUP BY "ADJUSTER_ID";


--
-- Name: vw_contractor_tracker; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_contractor_tracker AS
 SELECT "DECODED_CONTRACTOR" AS contractor,
    count(*) AS total_incidents,
    sum(("PAYOUT_AUTHORIZED")::numeric) AS total_payout_stolen,
    avg(("PREMIUM_SPIKE_USD")::numeric) AS avg_premium_spike
   FROM public.reit_portfolio
  WHERE (("DECODED_CONTRACTOR" IS NOT NULL) AND ("DECODED_CONTRACTOR" <> 'Standard_Vendor'::text))
  GROUP BY "DECODED_CONTRACTOR";


--
-- Name: vw_powerbi_dataset; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_powerbi_dataset AS
 WITH base AS (
         SELECT r."PROPERTY_ID",
            r."INCIDENT_DATE",
            r."MANAGER_ID",
            r."ADJUSTER_ID",
            r."PROPERTY_TYPE",
            r."CURRENCY_CODE",
            r."SQUARE_FOOTAGE",
            r."VALUATION_LOCAL",
            r."CURRENT_PREMIUM_LOCAL",
            r."BASE_PREMIUM_USD",
            r."INSURANCE_METADATA_JSON",
            r."YEAR",
            r."MONTH",
            r."QUARTER",
            r."INCIDENT_CLASSIFICATION",
            r."PAYOUT_AUTHORIZED",
            r."CONTRACTOR_A85",
            r."ADJUSTER_GRATUITY",
            r."DECODED_CONTRACTOR",
            r."EXCHANGE_RATE_USD",
            r."VALUATION_USD",
            r."CURRENT_PREMIUM_USD",
            r."PREMIUM_SPIKE_USD",
            r."PAYOUT_TO_VALUE_RATIO",
            r."PHANTOM_CLAIM_SUSPECT",
            r."ADJUSTER_KICKBACK_RATIO",
            r."TOTAL_FINANCIAL_DAMAGE_USD",
            r."COUNTRY_CODE",
                CASE
                    WHEN ((r."VALUATION_USD")::numeric > (10000000)::numeric) THEN 'Tier 1'::text
                    WHEN ((r."VALUATION_USD")::numeric >= (1000000)::numeric) THEN 'Tier 2'::text
                    ELSE 'Tier 3'::text
                END AS valuation_tier,
            ntile(10) OVER (ORDER BY (r."PAYOUT_AUTHORIZED")::numeric) AS payout_decile,
            sum((r."TOTAL_FINANCIAL_DAMAGE_USD")::numeric) OVER (PARTITION BY r."COUNTRY_CODE" ORDER BY r."INCIDENT_DATE", r."PROPERTY_ID" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total_damage_usd
           FROM public.reit_portfolio r
        ), fake_payout_rank AS (
         SELECT reit_portfolio."COUNTRY_CODE",
            reit_portfolio."ADJUSTER_ID",
            sum((reit_portfolio."PAYOUT_AUTHORIZED")::numeric) AS fake_payout_total,
            rank() OVER (PARTITION BY reit_portfolio."COUNTRY_CODE" ORDER BY (sum((reit_portfolio."PAYOUT_AUTHORIZED")::numeric)) DESC) AS adjuster_rank
           FROM public.reit_portfolio
          WHERE ((reit_portfolio."PHANTOM_CLAIM_SUSPECT")::integer = 1)
          GROUP BY reit_portfolio."COUNTRY_CODE", reit_portfolio."ADJUSTER_ID"
        ), first_corrupt_claim AS (
         SELECT reit_portfolio."PROPERTY_ID",
            row_number() OVER (PARTITION BY reit_portfolio."MANAGER_ID" ORDER BY reit_portfolio."INCIDENT_DATE", reit_portfolio."PROPERTY_ID") AS corrupt_claim_number
           FROM public.reit_portfolio
          WHERE ((reit_portfolio."PHANTOM_CLAIM_SUSPECT")::integer = 1)
        )
 SELECT b."PROPERTY_ID",
    b."INCIDENT_DATE",
    b."MANAGER_ID",
    b."ADJUSTER_ID",
    b."PROPERTY_TYPE",
    b."CURRENCY_CODE",
    b."SQUARE_FOOTAGE",
    b."VALUATION_LOCAL",
    b."CURRENT_PREMIUM_LOCAL",
    b."BASE_PREMIUM_USD",
    b."INSURANCE_METADATA_JSON",
    b."YEAR",
    b."MONTH",
    b."QUARTER",
    b."INCIDENT_CLASSIFICATION",
    b."PAYOUT_AUTHORIZED",
    b."CONTRACTOR_A85",
    b."ADJUSTER_GRATUITY",
    b."DECODED_CONTRACTOR",
    b."EXCHANGE_RATE_USD",
    b."VALUATION_USD",
    b."CURRENT_PREMIUM_USD",
    b."PREMIUM_SPIKE_USD",
    b."PAYOUT_TO_VALUE_RATIO",
    b."PHANTOM_CLAIM_SUSPECT",
    b."ADJUSTER_KICKBACK_RATIO",
    b."TOTAL_FINANCIAL_DAMAGE_USD",
    b."COUNTRY_CODE",
    b.valuation_tier,
    b.payout_decile,
    b.running_total_damage_usd,
    fpr.fake_payout_total,
    fpr.adjuster_rank,
        CASE
            WHEN (fcc.corrupt_claim_number = 1) THEN 1
            ELSE 0
        END AS first_corrupt_claim,
    at.total_bribes,
    at.unique_shell_companies,
    at.total_authorized_payouts AS adjuster_total_authorized_payouts,
    ct.total_incidents AS contractor_total_incidents,
    ct.total_payout_stolen AS contractor_total_payout_stolen,
    ct.avg_premium_spike AS contractor_avg_premium_spike
   FROM ((((base b
     LEFT JOIN fake_payout_rank fpr ON (((b."COUNTRY_CODE" = fpr."COUNTRY_CODE") AND (b."ADJUSTER_ID" = fpr."ADJUSTER_ID"))))
     LEFT JOIN first_corrupt_claim fcc ON ((b."PROPERTY_ID" = fcc."PROPERTY_ID")))
     LEFT JOIN public.mv_adjuster_tracker at ON ((b."ADJUSTER_ID" = at.adjuster_id)))
     LEFT JOIN public.mv_contractor_tracker ct ON ((b."DECODED_CONTRACTOR" = ct.contractor)));


--
-- Name: idx_reit_adjuster_incident; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reit_adjuster_incident ON public.reit_portfolio USING btree ("ADJUSTER_ID", "INCIDENT_DATE");

ALTER TABLE public.reit_portfolio CLUSTER ON idx_reit_adjuster_incident;


--
-- Name: idx_reit_contractor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reit_contractor ON public.reit_portfolio USING btree ("DECODED_CONTRACTOR");


--
-- Name: idx_reit_manager; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reit_manager ON public.reit_portfolio USING btree ("MANAGER_ID");


--
-- PostgreSQL database dump complete
--

\unrestrict fym08szTqUlafpMofJOSnjGgcQ4PBwYep8vVRnMuSZekepckoOLLVNlog1PQGhK

