/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/first-workflow',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'architecture/overview',
        'architecture/framework-integration',
        'architecture/business-logic-patterns',
        'architecture/event-system',
      ],
    },
    {
      type: 'category',
      label: 'Tutorials',
      items: [
        'tutorials/langchain-integration',
        'tutorials/temporal-workflows',
        'tutorials/mcp-toolkit',
        'tutorials/multi-framework-scenarios',
      ],
    },
    {
      type: 'category',
      label: 'Framework Adapters',
      items: [
        'adapters/langchain',
        'adapters/temporal',
        'adapters/mcp',
        'adapters/semantic-kernel',
        'adapters/fastmcp',
        'adapters/zep',
      ],
    },
    {
      type: 'category',
      label: 'Business Rules',
      items: [
        'rules/rule-syntax',
        'rules/rule-engine',
        'rules/examples',
        'rules/best-practices',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/reference',
        'api/orchestrator',
        'api/adapters',
        'api/events',
        'api/rules',
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/requirements',
        'deployment/docker',
        'deployment/kubernetes',
        'deployment/monitoring',
        'deployment/scaling',
      ],
    },
    {
      type: 'category',
      label: 'Community',
      items: [
        'community/contributing',
        'community/code-of-conduct',
        'community/governance',
        'community/roadmap',
      ],
    },
  ],

  // But you can create a sidebar manually
  /*
  tutorialSidebar: [
    'intro',
    'hello',
    {
      type: 'category',
      label: 'Tutorial',
      items: ['tutorial-basics/create-a-document'],
    },
  ],
   */
};

export default sidebars;