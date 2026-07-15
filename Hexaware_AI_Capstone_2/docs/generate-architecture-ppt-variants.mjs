import path from 'node:path';
import PptxGenJS from 'pptxgenjs';

const root = 'D:/Hexaware_AI_Capstone_2';
const docsDir = path.join(root, 'docs');
const architecturePng = path.join(docsDir, 'generated-diagrams', 'architecture-diagram.png');
const workflowPng = path.join(docsDir, 'generated-diagrams', 'workflow-diagram.png');

const colors = {
  bg: 'F8FAFC',
  title: '0F172A',
  text: '1E293B',
  accent: '1D4ED8',
  soft: 'DBEAFE'
};

function createDeckBase(title) {
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';
  pptx.author = 'Hexaware Demo Team';
  pptx.company = 'Hexaware';
  pptx.subject = title;
  pptx.title = title;
  pptx.lang = 'en-US';
  return pptx;
}

function addHeader(pptx, slide, title, subtitle = '') {
  slide.background = { color: colors.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.33,
    h: 0.65,
    fill: { color: colors.soft },
    line: { color: colors.soft }
  });
  slide.addText(title, {
    x: 0.6,
    y: 0.15,
    w: 11.5,
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

function addFooter(slide, deckLabel, index, total) {
  slide.addText(`${deckLabel} | Slide ${index} of ${total}`, {
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

async function createStakeholderDeck() {
  const totalSlides = 12;
  const pptx = createDeckBase('Form C Signup - Stakeholder View');
  let i = 0;

  i++;
  {
    const slide = pptx.addSlide();
    slide.background = { color: 'FFFFFF' };
    slide.addText('Form C Signup Solution', {
      x: 0.9,
      y: 1.8,
      w: 11,
      h: 0.9,
      fontFace: 'Calibri',
      bold: true,
      fontSize: 40,
      color: colors.title
    });
    slide.addText('Stakeholder-Focused Architecture and Workflow', {
      x: 0.9,
      y: 2.7,
      w: 12,
      h: 0.5,
      fontFace: 'Calibri',
      fontSize: 22,
      color: colors.accent
    });
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'Business Objective');
    addBullets(slide, [
      'Enable reliable digital signup with clear user experience.',
      'Reduce manual registration errors through validation at multiple layers.',
      'Provide a reusable baseline for onboarding-related workflows.',
      'Demonstrate scalable architecture foundation for future expansion.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'What Was Delivered');
    addBullets(slide, [
      'Frontend registration application for Form C signup.',
      'Backend API to process and validate signup requests.',
      'End-to-end error handling with user-friendly feedback.',
      'Automated quality checks for build confidence.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'High-Level Architecture');
    slide.addImage({ path: architecturePng, x: 0.8, y: 1.2, w: 11.8, h: 5.6 });
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'How Value Is Created');
    addBullets(slide, [
      'Fast and guided signup flow reduces user drop-off.',
      'Structured validations reduce downstream support effort.',
      'Consistent API contracts simplify future integrations.',
      'Clear modular separation lowers long-term change cost.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'End-to-End Workflow');
    slide.addImage({ path: workflowPng, x: 0.8, y: 1.2, w: 11.8, h: 5.6 });
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'User Experience Outcomes');
    addBullets(slide, [
      'Field-level validations prevent invalid submissions early.',
      'Clear success path gives confidence after registration.',
      'Meaningful errors for conflicts such as duplicate user id.',
      'Responsive, clean UI suitable for demos and pilot usage.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'Quality and Reliability');
    addBullets(slide, [
      'Backend validation, conflict handling, and health checks tested.',
      'Frontend functional behavior tested with automated UI tests.',
      'Lint/test/build gates executed for technical confidence.',
      'Structured responses improve monitoring and supportability.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'Demo Walkthrough Plan');
    addBullets(slide, [
      'Start backend and frontend services.',
      'Demonstrate empty form validation feedback.',
      'Demonstrate successful user registration flow.',
      'Demonstrate duplicate user conflict handling.',
      'Show resulting success confirmation page.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'Current Constraints');
    addBullets(slide, [
      'In-memory storage resets on restart (demo-oriented).',
      'No persistent database yet.',
      'Authentication token lifecycle not introduced yet.',
      'No deployment pipeline for production hosting yet.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'Roadmap and Business Impact');
    addBullets(slide, [
      'Add persistent data storage for production continuity.',
      'Introduce secure authentication and authorization.',
      'Implement CI/CD quality gates for rapid safe releases.',
      'Scale architecture for additional onboarding use cases.'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  i++;
  {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, 'Decision and Ask');
    addBullets(slide, [
      'Approve next phase for persistence and production hardening.',
      'Prioritize auth and deployment readiness in sprint planning.',
      'Align demo success criteria with pilot rollout objectives.',
      'Q&A'
    ]);
    addFooter(slide, 'Stakeholder Deck', i, totalSlides);
  }

  await pptx.writeFile({ fileName: path.join(docsDir, 'architecture-workflow-stakeholder.pptx') });
}

async function createTechnicalDeck() {
  const totalSlides = 15;
  const pptx = createDeckBase('Form C Signup - Technical Deep Dive');
  let i = 0;

  i++;
  {
    const slide = pptx.addSlide();
    slide.background = { color: 'FFFFFF' };
    slide.addText('Form C Signup', {
      x: 0.9,
      y: 1.7,
      w: 11,
      h: 0.8,
      fontFace: 'Calibri',
      fontSize: 38,
      bold: true,
      color: colors.title
    });
    slide.addText('Technical Deep-Dive: Architecture and Workflow', {
      x: 0.9,
      y: 2.6,
      w: 12,
      h: 0.5,
      fontFace: 'Calibri',
      fontSize: 22,
      color: colors.accent
    });
    addFooter(slide, 'Technical Deck', i, totalSlides);
  }

  const slides = [
    {
      t: 'Tech Stack and Runtime',
      b: [
        'Backend: Node.js + Express (ES modules).',
        'Frontend: React + Vite + React Router.',
        'Testing: Vitest/Supertest (backend), Jest/RTL (frontend).',
        'Styling: CSS Modules in frontend feature components.'
      ]
    },
    {
      t: 'Repository Structure',
      b: [
        'Backend root hosts API runtime and tests.',
        'Frontend isolated under frontend/ with independent scripts.',
        'docs/ contains architecture, workflow, and generated collateral.',
        '.github/ contains custom instruction and agent definitions.'
      ]
    },
    {
      t: 'Architecture Diagram',
      img: architecturePng,
      subtitle: 'User → React UI → Express API → Validation → Service → In-memory store'
    },
    {
      t: 'Backend Request Pipeline',
      b: [
        'src/server.js starts HTTP process and environment config.',
        'src/app.js wires helmet, cors, json parser, and morgan.',
        'Route mounts at /api/v1/auth via auth.routes.js.',
        'Global not-found and error middleware finalize pipeline.'
      ]
    },
    {
      t: 'Backend Module Deep Dive',
      b: [
        'auth.validator.js enforces payload boundary validation.',
        'auth.controller.js handles orchestration and response mapping.',
        'auth.service.js handles business logic and password hashing.',
        'utils/response.js enforces stable JSON envelope contract.'
      ]
    },
    {
      t: 'Signup API Contract',
      b: [
        'POST /api/v1/auth/signup',
        '201 on success with success/data/error envelope.',
        '400 on validation errors with detail array.',
        '409 USER_ID_ALREADY_EXISTS on duplicate conflicts.'
      ]
    },
    {
      t: 'Frontend Composition',
      b: [
        'main.jsx bootstraps BrowserRouter + AuthProvider.',
        'AppRoutes.jsx maps /signup and /signup/success routes.',
        'SignupPage.jsx owns controlled form state and submit flow.',
        'authApi.js integrates with backend API and normalizes failures.'
      ]
    },
    {
      t: 'Workflow Diagram',
      img: workflowPng,
      subtitle: 'Validation split across client and server with clear failure branches'
    },
    {
      t: 'Validation and Error Strategy',
      b: [
        'Client validates format and required fields before network request.',
        'Server re-validates payload to enforce trust boundaries.',
        'Frontend displays field-level and form-level error messages.',
        'Error middleware provides safe standardized API error payloads.'
      ]
    },
    {
      t: 'Security and Reliability Notes',
      b: [
        'Password hashing uses scrypt with random salt per credential.',
        'Helmet secures common HTTP headers.',
        'CORS enables controlled cross-origin frontend calls.',
        'Consistent response model simplifies API consumption and diagnostics.'
      ]
    },
    {
      t: 'Test Strategy and Coverage',
      b: [
        'Backend tests: health, signup success, validation failure, duplicate conflict.',
        'Frontend tests: invalid form, success navigation, API failure handling.',
        'Quality gates include lint, test, and frontend build.',
        'Current verification runs are passing for demo baseline.'
      ]
    },
    {
      t: 'Known Gaps and Risks',
      b: [
        'In-memory store is non-persistent and non-distributed.',
        'No auth token/session lifecycle yet.',
        'No database migration/versioning model yet.',
        'No deployment automation or environment promotion workflow yet.'
      ]
    },
    {
      t: 'Technical Roadmap',
      b: [
        'Add persistent repository layer and durable storage.',
        'Introduce authN/authZ and secure session strategy.',
        'Add structured observability: logs, metrics, traces.',
        'Automate CI/CD gates and production release pipeline.'
      ]
    },
    {
      t: 'Q&A',
      b: [
        'Open topics: persistence approach, auth model, and deployment target.',
        'Decisions needed for production-readiness timeline.'
      ]
    }
  ];

  for (const item of slides) {
    i++;
    const slide = pptx.addSlide();
    addHeader(pptx, slide, item.t, item.subtitle || '');
    if (item.img) {
      slide.addImage({ path: item.img, x: 0.8, y: 1.2, w: 11.8, h: 5.6 });
    } else {
      addBullets(slide, item.b || []);
    }
    addFooter(slide, 'Technical Deck', i, totalSlides);
  }

  await pptx.writeFile({ fileName: path.join(docsDir, 'architecture-workflow-technical-deep-dive.pptx') });
}

await createStakeholderDeck();
await createTechnicalDeck();
console.log('Created: architecture-workflow-stakeholder.pptx');
console.log('Created: architecture-workflow-technical-deep-dive.pptx');
