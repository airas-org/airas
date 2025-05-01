import type {ReactNode} from 'react';
import styles from './styles.module.css';

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.fullScreenContainer}>
      <div className={styles.fullScreenImageContainer}>
        <img
          className={styles.fullScreenImage}
          src={require('@site/static/img/airas_long.png').default}
          alt="AIRAS Logo"
        />
      </div>
      <div className={styles.textContainer}>
        <h2 className={styles.textHeading}>AI Research Automation System</h2>
        <p className={styles.textDescription}>
        AIRAS is a framework for automating AI research. 
        It enables the efficient development of AI systems for conducting AI research.
        </p>
      </div>
    </section>
  );
}
