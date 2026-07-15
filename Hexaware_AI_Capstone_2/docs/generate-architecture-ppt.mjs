import fs from 'node:fs/promises';
import path from 'node:path';
import PptxGenJS from 'pptxgenjs';

const root = 'D:/Hexaware_AI_Capstone_2';
const mdPath = path.join(root, 'docs', 'architecture-workflow-demo.md');
const outDir = path.join(root, 'docs');
const diagramDir = path.join(outDir, 'generated-diagrams');
const outPpt = path.join(outDir, 'architecture-workflow-demo.pptx');

await fs.mkdir(diagramDir, { recursive: true });

const md = await fs.readFile(mdPath, 'utf-8');
const mermaidMatches = [...md.matchAll(/```mermaid\s*([\s\S]*?)```/g)];

if (mermaidMatches.length < 2) {
  throw new Error('Expected at least 2 Mermaid diagrams in markdown.');
}

async function renderMermaidToPng(diagramSource, outputPath) {
  const base64 = Buffer.from(diagramSource.trim(), 'utf8').toString('base64');
  const base64Url = base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  const url = `https://mermaid.ink/img/${base64Url}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch Mermaid image: ${response.status}`);
  }

  const buf = Buffer.from(await response.arrayBuffer());
  await fs.writeFile(outputPath, buf);
}

const architecturePng = path.join(diagramDir, 'architecture-diagram.png');
const workflowPng = path.join(diagramDir, 'workflow-diagram.png');

await renderMermaidToPng(mermaidMatches[0][1], architecturePng);
await renderMermaidToPng(mermaidMatches[1][1], workflowPng);

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Hexaware Demo Team';
pptx.company = 'Hexaware';
pptx.subject = 'Architecture and Workflow Demo';
pptx.title = 'Form C Signup - Architecture and Workflow';
pptx.lang = 'en-US';

const colors = {
  bg: 'F7FAFC',
  title: '0F172A',
  text: '1E293B',
  accent: '1D4ED8',
  soft: 'DBEAFE'
};

function addHeader(slide, title, subtitle = '') {
  slide.background = { color: colors.bg };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.65, fill: { color: colors.soft }, line: { color: colors.soft } });
  slide.addText(title, {
    x: 0.6,
    y: 0.15,
    w: 10.8,
    h: 0.4,
    fontFace: 'Calibri',
    fontSize: 22,
    bold: true,
    color: colors.title
  });

  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6,
      y: 0.72,
      w: 12,
      h: 0.35,
      fontFace: 'Calibri',
      fontSize: 12,
      color: colors.accent
    });
  }
}

function addBullets(slide, bullets, x = 0.8, y = 1.3, w = 11.9, h = 5.6) {
  const runs = bullets.map((b) => ({
    text: b,
    options: { bullet: { indent: 16 }, hanging: 3, breakLine: true }
  }));

  slide.addText(runs, {
    x,
    y,
    w,
    h,
    fontFace: 'Calibri',
    fontSize: 18,
    color: colors.text,
    valign: 'top'
  });
}

function addFooter(slide, index) {
  slide.addText(`Demo Deck | Slide ${index} of 15`, {
    x: 0.6,
    y: 7.1,
    w: 12,
    h: 0.25,
    fontFace: 'Calibri',
    fontSize: 10,
    color: '64748B',
    align: 'right'
  });
}

let s = 0;

// 1
s++;
{
  const slide = pptx.addSlide();
  slide.background = { color: 'FFFFFF' };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 7.5, fill: { color: colors.bg }, line: { color: colors.bg } });
  slide.addText('Form C Signup Project', {
    x: 0.9,
    y: 1.7,
    w: 11.5,
    h: 0.9,
    fontFace: 'Calibri',
    bold: true,
    fontSize: 40,
    color: colors.title
  });
  slide.addText('Architecture and Workflow Demo', {
    x: 0.9,
    y: 2.6,
    w: 10.5,
    h: 0.55,
    fontFace: 'Calibri',
    fontSize: 24,
    color: colors.accent
  });
  slide.addText('Node.js Express Backend + React Frontend', {
    x: 0.9,
    y: 3.3,
    w: 11,
    h: 0.4,
    fontFace: 'Calibri',
    fontSize: 16,
    color: colors.text
  });
  addFooter(slide, s);
}

// 2
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Agenda');
  addBullets(slide, [
    '1. Project Purpose and Scope',
    '2. Solution Overview',
    '3. System Architecture Diagram',
    '4. Backend Architecture',
    '5. Frontend Architecture',
    '6. End-to-End Workflow Diagram',
    '7. Quality and Testing Workflow',
    '8. Demo Runbook, Limitations, and Next Steps'
  ]);
  addFooter(slide, s);
}

// 3
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Purpose and Demo Objective');
  addBullets(slide, [
    'Explain architecture and runtime workflow of the Form C Signup solution.',
    'Demonstrate an end-to-end signup journey from UI to backend service.',
    'Show key engineering practices: validation, error handling, and testing.',
    'Provide a ready script for technical and stakeholder demo conversations.'
  ]);
  addFooter(slide, s);
}

// 4
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Solution Overview');
  addBullets(slide, [
    'Full-stack JavaScript application with separated frontend and backend.',
    'Backend API built using Node.js and Express.',
    'Frontend web app built using React and Vite.',
    'Signup flow integrated end to end with consistent JSON response envelope.',
    'Layered backend and feature-oriented frontend organization.'
  ]);
  addFooter(slide, s);
}

// 5 - Architecture diagram
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'High-Level Architecture Diagram', 'Frontend ↔ Backend ↔ Validation/Service/Data');
  slide.addImage({ path: architecturePng, x: 0.7, y: 1.2, w: 12.0, h: 5.6 });
  addFooter(slide, s);
}

// 6
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Backend Architecture Layers');
  addBullets(slide, [
    'Entry/Boot: src/server.js',
    'App Wiring and Middleware: src/app.js',
    'Route Layer: src/features/auth/auth.routes.js',
    'Validation Layer: src/features/auth/auth.validator.js',
    'Controller Layer: src/features/auth/auth.controller.js',
    'Service Layer: src/features/auth/auth.service.js',
    'Error Middleware: src/middleware/error-handler.js and not-found.js'
  ]);
  addFooter(slide, s);
}

// 7
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Backend Technical Highlights');
  addBullets(slide, [
    'Security middleware via helmet and request logging via morgan.',
    'CORS enabled for frontend-backend communication.',
    'Passwords hashed using scrypt with per-user random salt.',
    'Duplicate user id detection with explicit conflict response.',
    'Demo data persistence currently uses in-memory Map storage.'
  ]);
  addFooter(slide, s);
}

// 8
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'API Contract - Signup');
  addBullets(slide, [
    'Endpoint: POST /api/v1/auth/signup',
    'Success Envelope: { success: true, data: { user }, error: null }',
    'Validation Failure: 400 with structured error details.',
    'Duplicate User ID: 409 with USER_ID_ALREADY_EXISTS code.',
    'Consistent error payload supports predictable frontend handling.'
  ]);
  addFooter(slide, s);
}

// 9
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Frontend Architecture');
  addBullets(slide, [
    'App Entry: frontend/src/main.jsx',
    'Routing: frontend/src/app/AppRoutes.jsx',
    'Signup Feature: frontend/src/features/signup/SignupPage.jsx',
    'Success Page: frontend/src/pages/SignupSuccessPage.jsx',
    'Auth Context: frontend/src/context/AuthContext.jsx',
    'API Client: frontend/src/services/authApi.js'
  ]);
  addFooter(slide, s);
}

// 10
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Frontend Design Decisions');
  addBullets(slide, [
    'Functional components and React Router-based page flow.',
    'Local state for form handling + React Context for shared user state.',
    'Client-side validation for immediate user feedback.',
    'CSS Modules for scoped styling and maintainable UI structure.',
    'Accessible labels and field/form error feedback patterns.'
  ]);
  addFooter(slide, s);
}

// 11 - workflow diagram
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'End-to-End Workflow Diagram', 'Signup journey across UI, API, validation, and service layers');
  slide.addImage({ path: workflowPng, x: 0.7, y: 1.2, w: 12.0, h: 5.6 });
  addFooter(slide, s);
}

// 12
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Quality and Testing Workflow');
  addBullets(slide, [
    'Backend checks: npm run lint and npm test.',
    'Backend coverage includes health, signup success, validation, and duplicate conflict.',
    'Frontend checks: lint, jest tests, and production build.',
    'Frontend coverage includes form validation, successful signup, and API failure handling.',
    'Verification pipeline executed successfully for demo readiness.'
  ]);
  addFooter(slide, s);
}

// 13
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Demo Runbook');
  addBullets(slide, [
    'Start backend: npm run start (project root).',
    'Start frontend: cd frontend and npm run dev.',
    'Open frontend at http://localhost:5173 and backend health at http://localhost:3000/health.',
    'Demo steps: empty form validation, valid signup, success navigation, duplicate user conflict.'
  ]);
  addFooter(slide, s);
}

// 14
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Current Limitations (Demo Scope)');
  addBullets(slide, [
    'Data persistence is in-memory and resets on backend restart.',
    'Database integration is not implemented yet.',
    'Authentication token/session lifecycle is pending.',
    'Production deployment pipeline documentation is pending.'
  ]);
  addFooter(slide, s);
}

// 15
s++;
{
  const slide = pptx.addSlide();
  addHeader(slide, 'Next Phase and Q&A');
  addBullets(slide, [
    'Introduce persistent storage layer (SQL or NoSQL).',
    'Add authentication and authorization flows.',
    'Add observability: structured logs, metrics, and tracing.',
    'Add CI quality gates for frontend and backend.',
    'Add non-functional suites: security and performance testing.',
    'Q&A'
  ]);
  addFooter(slide, s);
}

await pptx.writeFile({ fileName: outPpt });
console.log(`Created: ${outPpt}`);
