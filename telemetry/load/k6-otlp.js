import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    baseline: {executor: "constant-arrival-rate", rate: Number(__ENV.RATE || 100), timeUnit: "1s", duration: __ENV.DURATION || "2m", preAllocatedVUs: 20, maxVUs: 200},
  },
  thresholds: {http_req_failed: ["rate<0.001"], http_req_duration: ["p(99)<1000"]},
};

export default function () {
  const sequence = `${__VU}-${__ITER}-${Date.now()}`;
  const body = JSON.stringify({resourceLogs: [{resource: {attributes: [{key: "service.name", value: {stringValue: "aria-loadgen"}}, {key: "tenant.id", value: {stringValue: __ENV.TENANT || "loadtest"}}]}, scopeLogs: [{logRecords: [{timeUnixNano: `${Date.now()}000000`, severityText: "INFO", body: {stringValue: `aria load event sequence=${sequence}`}, attributes: [{key: "aria.sequence", value: {stringValue: sequence}}]}]}]}]});
  const response = http.post(`${__ENV.OTLP_HTTP || "http://localhost:4318"}/v1/logs`, body, {headers: {"Content-Type": "application/json"}});
  check(response, {"OTLP accepted": (r) => r.status === 200});
}
