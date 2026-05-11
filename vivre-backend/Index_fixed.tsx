import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { BellRing, Plus, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { PatientCard } from "@/components/vivre/PatientCard";
import { Skeleton } from "@/components/vivre/Skeleton";
import { Chatbot } from "@/components/vivre/Chatbot";
import { DEMO_PATIENTS, DEMO_VITALS, DEMO_ALERTS } from "@/lib/demo-data";

const VITAL_KEYS = ["heart_rate", "spo2", "blood_pressure"] as const;

function statusFor(metric: string, value: number): "ok" | "warn" | "crit" {
  if (metric === "heart_rate") return value < 50 || value > 110 ? "crit" : value < 60 || value > 100 ? "warn" : "ok";
  if (metric === "spo2") return value < 90 ? "crit" : value < 94 ? "warn" : "ok";
  if (metric === "blood_pressure") return value > 150 ? "crit" : value > 130 ? "warn" : "ok";
  return "ok";
}

async function loadPatients() {
  const { data: patients, error } = await supabase.from("patients").select("*");
  if (error || !patients || patients.length === 0) {
    return DEMO_PATIENTS.map((p) => decoratePatient(p, DEMO_VITALS[p.id] ?? [], DEMO_ALERTS[p.id] ?? []));
  }
  const ids = patients.map((p: any) => p.id);
  const [{ data: vitals }, { data: alerts }] = await Promise.all([
    supabase.from("vitals_readings").select("*").in("patient_id", ids).order("timestamp", { ascending: false }),
    supabase.from("alerts").select("*").in("patient_id", ids).eq("acknowledged", false),
  ]);
  return patients.map((p: any) => {
    const pv = (vitals ?? []).filter((v: any) => v.patient_id === p.id);
    const pa = (alerts ?? []).filter((a: any) => a.patient_id === p.id);
    return decoratePatient(p, pv, pa);
  });
}

function decoratePatient(p: any, vitals: any[], alerts: any[]) {
  const vmap: Record<string, any> = {};

  const latest = vitals[0];
  if (latest) {
    vmap["heart_rate"] = {
      value: Math.round(latest.heart_rate ?? 0),
      status: statusFor("heart_rate", latest.heart_rate ?? 0),
    };
    vmap["spo2"] = {
      value: Math.round(latest.spo2 ?? 0),
      status: statusFor("spo2", latest.spo2 ?? 0),
    };
    if (latest.systolic_bp != null && latest.diastolic_bp != null) {
      vmap["blood_pressure"] = {
        value: `${Math.round(latest.systolic_bp)}/${Math.round(latest.diastolic_bp)}`,
        status: statusFor("blood_pressure", latest.systolic_bp),
      };
    }
  }

  const hrHistory = vitals
    .filter((v: any) => v.heart_rate != null)
    .map((v: any) => Math.round(v.heart_rate))
    .slice(0, 20)
    .reverse();

  return {
    ...p,
    health_score: latest?.health_score ?? p.health_score ?? 0,
    predicted_condition: latest?.predicted_disease ?? p.predicted_condition ?? "",
    updated_at: latest?.timestamp ?? p.updated_at,
    vitals: vmap,
    hr_history: hrHistory,
    has_unack_alert: alerts.length > 0,
  };
}

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Vivre — Dashboard" },
      { name: "description", content: "Live overview of everyone you care about." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const { data: initialPatients = [], isLoading } = useQuery({
    queryKey: ["patients"],
    queryFn: loadPatients,
  });
  const [patients, setPatients] = useState<any[]>([]);
  const [flashIds, setFlashIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (initialPatients && initialPatients.length) setPatients(initialPatients);
  }, [initialPatients]);

  const computeStatus = (metric: string, value: number): "ok" | "warn" | "crit" => {
    if (metric === "heart_rate") {
      if (value < 50 || value > 120) return "crit";
      if (value > 100) return "warn";
      return "ok";
    }
    if (metric === "spo2") {
      if (value < 90) return "crit";
      if (value < 94) return "warn";
      return "ok";
    }
    if (metric === "blood_pressure") {
      if (value > 180) return "crit";
      if (value > 160) return "warn";
      return "ok";
    }
    return "ok";
  };

  useEffect(() => {
    const channel = supabase
      .channel("vitals-feed")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "vitals_readings" },
        (payload: any) => {
          const row = payload?.new ?? {};
          const pid = row.patient_id;
          if (!pid) return;

          if (row.is_anomaly || (row.alerts_triggered ?? 0) > 0) {
            setFlashIds((prev) => new Set(prev).add(pid));
            setTimeout(() => {
              setFlashIds((prev) => {
                const next = new Set(prev);
                next.delete(pid);
                return next;
              });
            }, 900);
          }

          setPatients((prev) =>
            prev.map((p) => {
              if (p.id !== pid) return p;

              const nextVitals = { ...(p.vitals ?? {}) };

              if (row.heart_rate != null) {
                const hr = Number(row.heart_rate);
                nextVitals["heart_rate"] = { value: Math.round(hr), status: computeStatus("heart_rate", hr) };
              }
              if (row.spo2 != null) {
                const sp = Number(row.spo2);
                nextVitals["spo2"] = { value: Math.round(sp), status: computeStatus("spo2", sp) };
              }
              if (row.systolic_bp != null && row.diastolic_bp != null) {
                nextVitals["blood_pressure"] = {
                  value: `${Math.round(row.systolic_bp)}/${Math.round(row.diastolic_bp)}`,
                  status: computeStatus("blood_pressure", row.systolic_bp),
                };
              }

              const hrVal = Number(row.heart_rate);
              const hr_history = Number.isFinite(hrVal)
                ? [...(p.hr_history ?? []), Math.round(hrVal)].slice(-20)
                : p.hr_history ?? [];

              return {
                ...p,
                health_score: row.health_score ?? p.health_score,
                predicted_condition: row.predicted_disease ?? p.predicted_condition,
                updated_at: row.timestamp ?? new Date().toISOString(),
                vitals: nextVitals,
                hr_history,
              };
            })
          );
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  const criticalCount = patients.filter((p: any) => (p.health_score ?? 100) < 40).length;

  return (
    <div className="mx-auto max-w-6xl px-4 md:px-10" style={{ paddingTop: 48, paddingBottom: 48 }}>
      <header className="flex items-start justify-between gap-4">
        <div>
          <div
            className="flex items-center gap-2 text-[11px] font-medium uppercase"
            style={{ letterSpacing: "0.2em", color: "#06B6D4" }}
          >
            <motion.span
              animate={{ rotate: [0, 12, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="inline-flex"
            >
              <Sun className="h-3.5 w-3.5" />
            </motion.span>
            Good morning
          </div>
          <h1 className="font-display mt-2 text-text-primary" style={{ fontSize: 48, fontWeight: 700, lineHeight: 1.05, letterSpacing: "-0.02em" }}>
            Lakshya
          </h1>
          <p className="mt-3 flex items-center gap-2 text-[13px] text-text-secondary">
            <span className="relative inline-flex h-2 w-2">
              <span className="absolute inset-0 animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
            </span>
            {patients.length} loved {patients.length === 1 ? "one" : "ones"} · monitoring live
          </p>
        </div>
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            className="relative flex h-10 w-10 items-center justify-center rounded-xl glass"
            aria-label="Notifications"
          >
            <BellRing className="h-4 w-4 text-text-secondary" />
            {criticalCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-status-crit px-1 text-[9px] font-bold text-white">
                {criticalCount}
              </span>
            )}
          </motion.button>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-violet-500 font-semibold text-white">
            L
          </div>
        </div>
      </header>

      <AnimatePresence>
        {criticalCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-5 inline-flex items-center gap-2.5 rounded-full px-3.5 py-1.5"
            style={{ background: "rgba(239,68,68,0.10)", border: "1px solid rgba(239,68,68,0.30)" }}
          >
            <span className="relative inline-flex h-2 w-2">
              <span className="absolute inset-0 animate-ping rounded-full bg-red-500 opacity-70" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
            </span>
            <span className="text-[12px] font-medium text-red-200">
              {criticalCount} patient{criticalCount > 1 ? "s require" : " requires"} immediate attention
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        variants={{ show: { transition: { staggerChildren: 0.08 } } }}
        initial="hidden"
        animate="show"
        className="grid items-start gap-5 sm:grid-cols-2 lg:grid-cols-3"
        style={{ marginTop: 32 }}
      >
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-64 rounded-2xl" />
            ))
          : patients.map((p: any) => (
              <PatientCard key={p.id} patient={p} flash={flashIds.has(p.id)} />
            ))}
      </motion.div>

      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 18, delay: 0.6 }}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        className="fixed bottom-44 left-4 z-40 flex items-center gap-2 rounded-full bg-cyan-500 px-4 py-3 text-sm font-medium text-[#06121a] shadow-[0_8px_24px_rgba(6,182,212,0.45)] md:bottom-6"
      >
        <Plus className="h-4 w-4" /> Add patient
      </motion.button>

      <Chatbot />
    </div>
  );
}
