import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Framework Agnostic',
    Svg: require('@site/static/img/framework-agnostic.svg').default,
    description: (
      <>
        Define business logic once and execute across LangChain, Temporal,
        MCP, Semantic Kernel, FastMCP, and Zep AI without changing your code.
      </>
    ),
  },
  {
    title: 'Enterprise Ready',
    Svg: require('@site/static/img/enterprise-ready.svg').default,
    description: (
      <>
        Production-grade with built-in monitoring, security, scalability,
        and comprehensive error handling for mission-critical workflows.
      </>
    ),
  },
  {
    title: 'Event-Driven Architecture',
    Svg: require('@site/static/img/event-driven.svg').default,
    description: (
      <>
        Asynchronous event coordination enables real-time communication
        between frameworks with persistence and replay capabilities.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}