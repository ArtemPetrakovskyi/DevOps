# DVO-L4-3C8B52
{{/*
Коротке ім'я чарта.
*/}}
{{- define "task-manager.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 40 | trimSuffix "-" }}
{{- end }}

{{/*
Повне ім'я об'єктів, побудоване з імені релізу (щоб чарт можна було встановити двічі).
Суфікс компонента (-api, -web, -db ...) додається в маніфестах.
*/}}
{{- define "task-manager.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 40 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 40 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 40 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Мітки-селектори. Аргумент: dict "ctx" . "component" "api"
*/}}
{{- define "task-manager.selectorLabels" -}}
app.kubernetes.io/name: {{ include "task-manager.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Повний набір міток (включно з маркуванням кафедри mascot).
Аргумент: dict "ctx" . "component" "api"
*/}}
{{- define "task-manager.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .ctx.Chart.Name .ctx.Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "task-manager.selectorLabels" . }}
app.kubernetes.io/version: {{ .ctx.Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .ctx.Release.Service }}
app.kubernetes.io/part-of: task-manager
mascot: {{ .ctx.Values.mascot.label | quote }}
{{- end }}

{{/*
Анотації маркування кафедри (додаток А, п. А.3).
*/}}
{{- define "task-manager.annotations" -}}
devops-lab/mascot-approved: "true"
devops-lab/mascot: "гарбуз"
{{- end }}
