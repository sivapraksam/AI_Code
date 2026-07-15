import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import styles from './SignupSuccessPage.module.css';

export default function SignupSuccessPage() {
  const { user } = useAuth();

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="signup-success-heading">
        <h1 id="signup-success-heading">Registration Completed</h1>
        <p>Your account has been created successfully.</p>
        {user ? <p className={styles.meta}>User ID: {user.userId}</p> : null}
        <Link to="/signup" className={styles.link}>
          Register another user
        </Link>
      </section>
    </main>
  );
}
