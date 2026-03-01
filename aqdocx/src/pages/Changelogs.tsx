import { useTheme } from '../context/ThemeContext'
import { Link } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { FileText, Tag, ArrowRight, CheckCircle, Zap, Bug, Wrench, AlertTriangle, Shield, Brain, Database, Terminal, Layers, Box, Sparkles } from 'lucide-react'

interface ChangelogEntry {
  version: string
  date: string
  tag: 'major' | 'minor' | 'patch'
  highlights?: string
  sections: {
    title: string
    icon: React.ReactNode
    items: string[]
  }[]
}

const changelogs: ChangelogEntry[] = [
  {
    version: '2.0.0',
    date: '2025-06-01',
    tag: 'major',
    highlights: 'Manifest-First Architecture, Aquilary Registry, .crous Artifacts, Complete CLI Rewrite',
    sections: [
      {
        title: 'Breaking Changes',
        icon: <AlertTriangle className="w-4 h-4 text-red-500" />,
        items: [
          'Complete rewrite to Manifest-First Architecture — workspace.py replaces settings.py',
          'Module system now uses AppManifest declarations with explicit imports/exports',
          'DI container redesigned with Aquilary registry and scope-aware injection',
          'Controller decorators renamed: @api_route → @Get/@Post/@Put/@Delete etc.',
          'Config system moved from Django-style settings to workspace.py + module manifests',
          'Middleware pipeline now uses Aquilia native middleware protocol',
          'Database ORM now uses Aquilia models with blueprint projections',
          'Authentication redesigned with pluggable AuthManager and guard system',
        ],
      },
      {
        title: 'New Features',
        icon: <Sparkles className="w-4 h-4 text-aquilia-500" />,
        items: [
          'Aquilary Registry — compile-time module graph validation with dependency resolution',
          '.crous artifact format — compiled, signed, fingerprinted deployment artifacts',
          'Effects system — declarative side-effect composition with @Effect decorators',
          'Blueprint system — schema projections, lenses, facets, and annotations',
          'Fault system — domain-driven error handling with FaultDomain hierarchy',
          'Cache subsystem — multi-backend (Redis, Memory, Composite L1/L2) with decorators',
          'WebSocket subsystem — rooms, channels, adapters, binary protocol support',
          'Mail subsystem — provider chain, DKIM, TLS, template rendering',
          'Session subsystem — cookie/header/JWT stores with flash messages',
          'Trace subsystem — distributed tracing, span management, diagnostics',
          'MLOps subsystem — model packaging, serving, drift detection, experiment tracking',
          'Complete CLI rewrite (aq v2.0.0) with 30+ commands across 9 categories',
          'Auto-discovery engine — AST-based component scanning with manifest sync',
          'Deployment generators — Dockerfile, Docker Compose, Kubernetes, Nginx, CI/CD',
        ],
      },
      {
        title: 'CLI',
        icon: <Terminal className="w-4 h-4 text-green-500" />,
        items: [
          'New command: aq doctor — 6-phase workspace health diagnostics',
          'New command: aq discover — AST-based auto-discovery with --sync mode',
          'New command: aq analytics — workspace health scoring and dependency analysis',
          'New command: aq deploy — 9 deployment artifact generators',
          'New command: aq artifact — artifact lifecycle management (list/inspect/verify/gc)',
          'New command: aq trace — trace status, journal, diff, inspection',
          'New command: aq ws — WebSocket inspection, broadcast, client generation',
          'New command: aq cache — cache check, inspect, stats, clear',
          'New command: aq mail — mail check, send-test, inspect',
          'New command: aq test — Aquilia-aware pytest runner with auto-discovery',
          'New command: aq freeze — compile + SHA-256 fingerprinted frozen.json',
          'New command: aq manifest update — AST-based manifest scanning and updating',
          'MLOps commands: aq pack/model/deploy/observe/export/plugin/lineage/experiment',
        ],
      },
      {
        title: 'DI & Data',
        icon: <Database className="w-4 h-4 text-purple-500" />,
        items: [
          'Scope-aware injection: Singleton, Request, Transient lifecycles',
          'Provider types: Class, Factory, Value, Existing, Async providers',
          'Conditional binding with @ConditionalOn decorators',
          'Auto-wiring with type-hint resolution',
          'Blueprint projections for read/write model separation',
          'Schema-driven serialization with nested blueprint support',
        ],
      },
      {
        title: 'Security',
        icon: <Shield className="w-4 h-4 text-blue-500" />,
        items: [
          'AuthManager with pluggable authentication strategies',
          'Guard system — CanActivate, RoleGuard, PermissionGuard, CompositeGuard',
          'JWT + Session hybrid authentication',
          'OAuth2 integration with provider abstraction',
          'MFA support with TOTP/backup codes',
          'CORS middleware with fine-grained configuration',
          'Policy-based authorization with PolicyEngine',
        ],
      },
    ],
  },
  {
    version: '1.5.0',
    date: '2025-03-15',
    tag: 'minor',
    highlights: 'WebSocket support, Cache decorators, Mail subsystem preview',
    sections: [
      {
        title: 'Features',
        icon: <Zap className="w-4 h-4 text-aquilia-500" />,
        items: [
          'WebSocket support with room management and binary protocols',
          'Cache decorator system with TTL and namespace support',
          'Mail subsystem preview with SMTP and console backends',
          'Session flash messages',
          'Template engine with Jinja2 integration',
        ],
      },
      {
        title: 'Improvements',
        icon: <Wrench className="w-4 h-4 text-yellow-500" />,
        items: [
          'Improved error messages in DI resolution failures',
          'Better route specificity scoring algorithm',
          'Faster workspace compilation with incremental builds',
          'Reduced memory usage in artifact store',
        ],
      },
      {
        title: 'Bug Fixes',
        icon: <Bug className="w-4 h-4 text-red-500" />,
        items: [
          'Fixed middleware ordering in nested module pipelines',
          'Fixed race condition in async DI provider initialization',
          'Fixed route parameter parsing with special characters',
          'Fixed session cookie SameSite attribute on cross-origin requests',
        ],
      },
    ],
  },
  {
    version: '1.4.0',
    date: '2025-01-20',
    tag: 'minor',
    highlights: 'MLOps preview, Blueprint projections, Improved CLI',
    sections: [
      {
        title: 'Features',
        icon: <Zap className="w-4 h-4 text-aquilia-500" />,
        items: [
          'MLOps subsystem preview — model packaging with aq pack',
          'Blueprint projections for read-model separation',
          'Fault domain hierarchy with automatic HTTP status mapping',
          'CLI: aq inspect config command',
          'CLI: aq inspect faults command',
        ],
      },
      {
        title: 'Improvements',
        icon: <Wrench className="w-4 h-4 text-yellow-500" />,
        items: [
          'Faster AST-based manifest parsing',
          'Improved workspace validation with strict mode',
          'Better TypeScript client generation for WebSocket endpoints',
        ],
      },
    ],
  },
  {
    version: '1.3.0',
    date: '2024-11-10',
    tag: 'minor',
    highlights: 'Effects system, Trace subsystem, Artifact verification',
    sections: [
      {
        title: 'Features',
        icon: <Zap className="w-4 h-4 text-aquilia-500" />,
        items: [
          'Effects system with @Effect decorators and composition',
          'Trace subsystem with distributed span management',
          'Artifact verification with SHA-256 integrity checks',
          'CLI: aq artifact verify-all command',
          'CLI: aq trace journal with event filtering',
        ],
      },
      {
        title: 'Bug Fixes',
        icon: <Bug className="w-4 h-4 text-red-500" />,
        items: [
          'Fixed circular dependency detection in module graph',
          'Fixed hot-reload crash on manifest syntax errors',
          'Fixed artifact export including stale .crous files',
        ],
      },
    ],
  },
  {
    version: '1.2.0',
    date: '2024-09-05',
    tag: 'minor',
    highlights: 'Auto-discovery engine, Doctor command, Analytics',
    sections: [
      {
        title: 'Features',
        icon: <Zap className="w-4 h-4 text-aquilia-500" />,
        items: [
          'Auto-discovery engine with AST-based component scanning',
          'aq doctor command with 6-phase diagnostics',
          'aq analytics command with health scoring',
          'aq discover --sync for automatic manifest updates',
          'Deployment generators for Docker, Compose, Kubernetes',
        ],
      },
    ],
  },
  {
    version: '1.1.0',
    date: '2024-07-15',
    tag: 'minor',
    highlights: 'Improved DI, Auth guards, OpenAPI generation',
    sections: [
      {
        title: 'Features',
        icon: <Zap className="w-4 h-4 text-aquilia-500" />,
        items: [
          'Guard system with RoleGuard and PermissionGuard',
          'OpenAPI 3.1 spec generation from controller decorators',
          'Async DI provider support',
          'Module-scoped DI containers',
        ],
      },
    ],
  },
  {
    version: '1.0.0',
    date: '2024-05-01',
    tag: 'major',
    highlights: 'Initial stable release of Aquilia Framework',
    sections: [
      {
        title: 'Features',
        icon: <CheckCircle className="w-4 h-4 text-green-500" />,
        items: [
          'Manifest-First Architecture with workspace.py',
          'Module system with AppManifest declarations',
          'Controller system with HTTP method decorators',
          'DI container with type-hint auto-wiring',
          'Aquilary registry with compile-time validation',
          'ASGI server with uvicorn integration',
          'CLI tooling: aq init, add, run, serve, compile, validate, inspect',
          'Database integration with migration support',
        ],
      },
    ],
  },
]

export function Changelogs() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const tagColors = {
    major: 'bg-red-500/10 text-red-500 border-red-500/20',
    minor: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    patch: 'bg-green-500/10 text-green-500 border-green-500/20',
  }

  return (
    <div className={`min-h-screen ${isDark ? 'bg-[#09090b] text-white' : 'bg-gray-50 text-gray-900'}`}>
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        {/* Header */}
        <div className="mb-16 text-center">
          <div className="flex items-center justify-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
            <FileText className="w-4 h-4" />
            Changelog
          </div>
          <h1 className="text-5xl font-bold tracking-tighter mb-4">
            <span className="gradient-text">Changelog</span>
          </h1>
          <p className={`text-lg max-w-xl mx-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            A detailed history of every change, feature, fix, and improvement shipped in Aquilia.
          </p>
          <div className="flex items-center justify-center gap-4 mt-6">
            <Link
              to="/releases"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-aquilia-500 border border-aquilia-500/30 hover:bg-aquilia-500/10 transition-colors"
            >
              <Tag className="w-4 h-4" />
              View Releases
            </Link>
            <a
              href="https://github.com/axiomchronicles/Aquilia"
              target="_blank"
              rel="noopener"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? 'text-gray-400 border border-white/10 hover:bg-white/5' : 'text-gray-600 border border-gray-200 hover:bg-gray-100'}`}
            >
              GitHub
            </a>
          </div>
        </div>

        {/* Split Layout */}
        <div className="space-y-16">
          {changelogs.map((entry, idx) => {
            const isEven = idx % 2 === 0
            const midpoint = Math.ceil(entry.sections.length / 2)
            const leftSections = entry.sections.slice(0, midpoint)
            const rightSections = entry.sections.slice(midpoint)

            return (
              <div key={entry.version}>
                {/* Version header bar */}
                <div className={`flex items-center justify-between flex-wrap gap-3 mb-6 px-4 py-3 rounded-xl border ${
                  entry.tag === 'major'
                    ? isDark ? 'bg-red-500/5 border-red-500/20' : 'bg-red-50 border-red-200'
                    : entry.tag === 'minor'
                    ? isDark ? 'bg-blue-500/5 border-blue-500/20' : 'bg-blue-50 border-blue-200'
                    : isDark ? 'bg-green-500/5 border-green-500/20' : 'bg-green-50 border-green-200'
                }`}>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold font-mono">v{entry.version}</h2>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${tagColors[entry.tag]}`}>
                      {entry.tag}
                    </span>
                  </div>
                  <time className={`text-sm font-medium ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{entry.date}</time>
                </div>

                {/* Highlights */}
                {entry.highlights && (
                  <p className={`text-sm mb-6 px-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    <Sparkles className="w-3.5 h-3.5 inline mr-1.5 text-aquilia-500" />
                    {entry.highlights}
                  </p>
                )}

                {/* Two-column split */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left column */}
                  <div className="space-y-5">
                    {leftSections.map((section, sIdx) => (
                      <div key={sIdx} className={`rounded-xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
                        <div className="flex items-center gap-2 mb-3">
                          {section.icon}
                          <h3 className={`text-sm font-bold uppercase tracking-wide ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                            {section.title}
                          </h3>
                        </div>
                        <ul className="space-y-2">
                          {section.items.map((item, iIdx) => (
                            <li key={iIdx} className="flex items-start gap-2">
                              <ArrowRight className={`w-3 h-3 mt-1 flex-shrink-0 ${isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                              <span className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>

                  {/* Right column */}
                  <div className="space-y-5">
                    {rightSections.map((section, sIdx) => (
                      <div key={sIdx} className={`rounded-xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
                        <div className="flex items-center gap-2 mb-3">
                          {section.icon}
                          <h3 className={`text-sm font-bold uppercase tracking-wide ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                            {section.title}
                          </h3>
                        </div>
                        <ul className="space-y-2">
                          {section.items.map((item, iIdx) => (
                            <li key={iIdx} className="flex items-start gap-2">
                              <ArrowRight className={`w-3 h-3 mt-1 flex-shrink-0 ${isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                              <span className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Divider between versions */}
                {idx < changelogs.length - 1 && (
                  <div className={`mt-16 border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`} />
                )}
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className="mt-16 text-center">
          <p className={`text-sm ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
            For older versions, see the <a href="https://github.com/axiomchronicles/Aquilia/releases" target="_blank" rel="noopener" className="text-aquilia-500 hover:underline">GitHub Releases</a> page.
          </p>
        </div>
      </div>
    </div>
  )
}
