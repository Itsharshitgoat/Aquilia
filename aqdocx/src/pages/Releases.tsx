import { useTheme } from '../context/ThemeContext'
import { Link } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { Tag, Download, Github, ArrowRight, CheckCircle, Clock, Package, Zap, Shield, Terminal, Brain, FileText, ExternalLink, Star, GitBranch } from 'lucide-react'

interface Release {
  version: string
  codename: string
  date: string
  status: 'latest' | 'stable' | 'lts' | 'eol'
  python: string
  highlights: string[]
  downloads: {
    pypi: string
    github: string
  }
  stats?: {
    commits: number
    contributors: number
    filesChanged: number
  }
}

const releases: Release[] = [
  {
    version: '2.0.0',
    codename: 'Phoenix',
    date: '2025-06-01',
    status: 'latest',
    python: '≥ 3.10',
    highlights: [
      'Complete Manifest-First Architecture rewrite',
      'Aquilary Registry with compile-time validation',
      '.crous artifact format for deployment',
      '30+ CLI commands across 9 categories',
      'MLOps subsystem with model packaging & serving',
      'Effects, Blueprints, Fault system',
      'WebSocket, Cache, Mail, Sessions, Trace subsystems',
      'Auto-discovery engine with AST-based scanning',
      'Deployment generators (Docker, K8s, CI/CD)',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/2.0.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v2.0.0',
    },
    stats: { commits: 1847, contributors: 12, filesChanged: 482 },
  },
  {
    version: '1.5.0',
    codename: 'Condor',
    date: '2025-03-15',
    status: 'stable',
    python: '≥ 3.10',
    highlights: [
      'WebSocket room management & binary protocols',
      'Cache decorator system with multi-backend',
      'Mail subsystem with provider chain',
      'Template engine with Jinja2 integration',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/1.5.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v1.5.0',
    },
    stats: { commits: 423, contributors: 8, filesChanged: 127 },
  },
  {
    version: '1.4.0',
    codename: 'Falcon',
    date: '2025-01-20',
    status: 'stable',
    python: '≥ 3.10',
    highlights: [
      'MLOps preview with model packaging',
      'Blueprint projections for CQRS patterns',
      'Fault domain hierarchy',
      'Enhanced CLI inspection commands',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/1.4.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v1.4.0',
    },
    stats: { commits: 312, contributors: 7, filesChanged: 98 },
  },
  {
    version: '1.3.0',
    codename: 'Hawk',
    date: '2024-11-10',
    status: 'stable',
    python: '≥ 3.10',
    highlights: [
      'Effects system with declarative composition',
      'Trace subsystem with distributed spans',
      'Artifact verification with SHA-256',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/1.3.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v1.3.0',
    },
    stats: { commits: 278, contributors: 6, filesChanged: 85 },
  },
  {
    version: '1.2.0',
    codename: 'Eagle',
    date: '2024-09-05',
    status: 'eol',
    python: '≥ 3.10',
    highlights: [
      'Auto-discovery engine',
      'Doctor command with 6-phase diagnostics',
      'Analytics and health scoring',
      'Deployment generators',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/1.2.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v1.2.0',
    },
    stats: { commits: 241, contributors: 5, filesChanged: 73 },
  },
  {
    version: '1.1.0',
    codename: 'Kestrel',
    date: '2024-07-15',
    status: 'eol',
    python: '≥ 3.10',
    highlights: [
      'Guard system (Role, Permission)',
      'OpenAPI 3.1 spec generation',
      'Async DI providers',
      'Module-scoped DI containers',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/1.1.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v1.1.0',
    },
    stats: { commits: 189, contributors: 4, filesChanged: 56 },
  },
  {
    version: '1.0.0',
    codename: 'Aquila',
    date: '2024-05-01',
    status: 'eol',
    python: '≥ 3.10',
    highlights: [
      'Initial stable release',
      'Manifest-First Architecture foundation',
      'Controller, DI, Routing, Server',
      'CLI tooling and database integration',
    ],
    downloads: {
      pypi: 'https://pypi.org/project/aquilia/1.0.0/',
      github: 'https://github.com/axiomchronicles/Aquilia/releases/tag/v1.0.0',
    },
    stats: { commits: 1024, contributors: 3, filesChanged: 312 },
  },
]

export function Releases() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const statusBadge = (status: Release['status']) => {
    const styles = {
      latest: 'bg-aquilia-500/10 text-aquilia-500 border-aquilia-500/20',
      stable: 'bg-green-500/10 text-green-500 border-green-500/20',
      lts: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      eol: `${isDark ? 'bg-white/5 text-gray-500 border-white/10' : 'bg-gray-100 text-gray-400 border-gray-200'}`,
    }
    const labels = { latest: 'Latest', stable: 'Stable', lts: 'LTS', eol: 'End of Life' }
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  return (
    <div className={`min-h-screen ${isDark ? 'bg-[#09090b] text-white' : 'bg-gray-50 text-gray-900'}`}>
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        {/* Header */}
        <div className="mb-16 text-center">
          <div className="flex items-center justify-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
            <Tag className="w-4 h-4" />
            Releases
          </div>
          <h1 className="text-5xl font-bold tracking-tighter mb-4">
            <span className="gradient-text">Releases</span>
          </h1>
          <p className={`text-lg max-w-xl mx-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Official releases of the Aquilia Framework. Each release is signed, tagged, and published to PyPI.
          </p>
          <div className="flex items-center justify-center gap-4 mt-6">
            <Link
              to="/changelogs"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-aquilia-500 border border-aquilia-500/30 hover:bg-aquilia-500/10 transition-colors"
            >
              <FileText className="w-4 h-4" />
              View Changelogs
            </Link>
          </div>
        </div>

        {/* Install Banner */}
        <div className={`mb-12 p-6 rounded-2xl border ${isDark ? 'bg-aquilia-500/5 border-aquilia-500/20' : 'bg-aquilia-50 border-aquilia-200'}`}>
          <div className="flex items-center gap-3 mb-3">
            <Download className="w-5 h-5 text-aquilia-500" />
            <h3 className="font-bold text-lg">Install Latest</h3>
          </div>
          <div className={`font-mono text-sm px-4 py-3 rounded-lg ${isDark ? 'bg-black/40' : 'bg-white'}`}>
            <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>$ </span>
            <span className={isDark ? 'text-green-400' : 'text-green-600'}>pip install</span>
            <span className={isDark ? 'text-white' : 'text-gray-900'}> aquilia</span>
          </div>
        </div>

        {/* Release Cards — Split Layout */}
        <div className="space-y-8">
          {releases.map((release, idx) => {
            const highlightMid = Math.ceil(release.highlights.length / 2)
            const leftHighlights = release.highlights.slice(0, highlightMid)
            const rightHighlights = release.highlights.slice(highlightMid)

            return (
              <div
                key={release.version}
                className={`rounded-2xl border overflow-hidden transition-all duration-300 ${
                  release.status === 'latest'
                    ? isDark
                      ? 'bg-[#0A0A0A] border-aquilia-500/30 shadow-lg shadow-aquilia-500/5'
                      : 'bg-white border-aquilia-300 shadow-lg shadow-aquilia-500/10'
                    : isDark
                    ? 'bg-[#0A0A0A] border-white/10'
                    : 'bg-white border-gray-200'
                }`}
              >
                {/* Card Header */}
                <div className={`px-6 py-5 border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <Package className={`w-5 h-5 ${release.status === 'latest' ? 'text-aquilia-500' : isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                        <h2 className="text-2xl font-bold font-mono">v{release.version}</h2>
                      </div>
                      <span className={`text-sm font-medium italic ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>"{release.codename}"</span>
                      {statusBadge(release.status)}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={`flex items-center gap-1.5 text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Clock className="w-3.5 h-3.5" />
                        {release.date}
                      </div>
                      <div className={`flex items-center gap-1.5 text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Terminal className="w-3.5 h-3.5" />
                        Python {release.python}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Body — Two-column split */}
                <div className="px-6 py-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left: highlights (first half) + stats */}
                    <div className="space-y-6">
                      <div>
                        <h4 className={`text-xs font-bold uppercase tracking-wide mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Highlights</h4>
                        <ul className="space-y-2">
                          {leftHighlights.map((h, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <CheckCircle className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${release.status === 'latest' ? 'text-aquilia-500' : 'text-green-500'}`} />
                              <span className={`text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{h}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {release.stats && (
                        <div>
                          <h4 className={`text-xs font-bold uppercase tracking-wide mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Stats</h4>
                          <div className="grid grid-cols-3 gap-2">
                            <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                              <div className="font-bold text-lg">{release.stats.commits.toLocaleString()}</div>
                              <div className={`text-[10px] uppercase tracking-wide ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Commits</div>
                            </div>
                            <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                              <div className="font-bold text-lg">{release.stats.contributors}</div>
                              <div className={`text-[10px] uppercase tracking-wide ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Authors</div>
                            </div>
                            <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                              <div className="font-bold text-lg">{release.stats.filesChanged}</div>
                              <div className={`text-[10px] uppercase tracking-wide ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Files</div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Right: highlights (second half) + downloads */}
                    <div className="space-y-6">
                      {rightHighlights.length > 0 && (
                        <div>
                          <h4 className={`text-xs font-bold uppercase tracking-wide mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>More</h4>
                          <ul className="space-y-2">
                            {rightHighlights.map((h, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <CheckCircle className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${release.status === 'latest' ? 'text-aquilia-500' : 'text-green-500'}`} />
                                <span className={`text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{h}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div>
                        <h4 className={`text-xs font-bold uppercase tracking-wide mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Download</h4>
                        <div className="space-y-2">
                          <a
                            href={release.downloads.pypi}
                            target="_blank"
                            rel="noopener"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? 'bg-white/5 text-gray-300 hover:bg-white/10' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
                          >
                            <Download className="w-3.5 h-3.5" />
                            PyPI
                            <ExternalLink className="w-3 h-3 ml-auto opacity-50" />
                          </a>
                          <a
                            href={release.downloads.github}
                            target="_blank"
                            rel="noopener"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isDark ? 'bg-white/5 text-gray-300 hover:bg-white/10' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
                          >
                            <Github className="w-3.5 h-3.5" />
                            GitHub Release
                            <ExternalLink className="w-3 h-3 ml-auto opacity-50" />
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className={`mt-16 text-center space-y-4`}>
          <div className="flex items-center justify-center gap-6">
            <a
              href="https://github.com/axiomchronicles/Aquilia"
              target="_blank"
              rel="noopener"
              className="flex items-center gap-2 text-sm text-aquilia-500 hover:underline"
            >
              <Star className="w-4 h-4" /> Star on GitHub
            </a>
            <a
              href="https://github.com/axiomchronicles/Aquilia/issues"
              target="_blank"
              rel="noopener"
              className={`flex items-center gap-2 text-sm hover:underline ${isDark ? 'text-gray-400' : 'text-gray-500'}`}
            >
              <GitBranch className="w-4 h-4" /> Report Issue
            </a>
          </div>
          <p className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
            All releases follow <a href="https://semver.org" target="_blank" rel="noopener" className="text-aquilia-500 hover:underline">Semantic Versioning 2.0.0</a>
          </p>
        </div>
      </div>
    </div>
  )
}
