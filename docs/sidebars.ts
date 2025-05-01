import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    {
      type: 'category',
      label: 'Get Started',
      items: ['introduction', 'quickstart'],
    },
    {
      type: 'category',
      label: 'Component',
      items: [
        'component/generator',
        'component/executor',
        'component/html-uploader',
        'component/analytic-subgraph',
        'component/experimental-plan-subgraph',
        'component/latex-subgraph',
        'component/readme-subgraph',
        'component/research-preparation-subgraph',
        'component/review-subgraph',
        'component/writer-subgraph',
      ],
    },
    {
      type: 'category',
      label: 'Development',
      items: [
        'development/local-setup',
        'development/roadmap',
        'development/MCP'
      ],
    },
  ],
};

export default sidebars;
