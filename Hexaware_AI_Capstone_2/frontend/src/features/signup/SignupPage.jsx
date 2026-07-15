import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { signup } from '../../services/authApi.js';
import styles from './SignupPage.module.css';

const DEFAULT_VALUES = {
  userId: '',
  password: '',
  confirmPassword: '',
  securityQuestion: '',
  securityAnswer: '',
  name: '',
  gender: '',
  dateOfBirth: '',
  occupation: '',
  email: '',
  mobile: '',
  nationality: 'INDIA'
};

function validate(values) {
  const errors = {};

  if (!/^(?=.*[A-Za-z])(?=.*\d).+$/.test(values.userId)) {
    errors.userId = 'User ID must include at least one letter and one number.';
  }

  if (values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  }

  if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9\s]).+$/.test(values.password)) {
    errors.password = 'Password must include uppercase, lowercase, number, and special character.';
  }

  if (values.confirmPassword !== values.password) {
    errors.confirmPassword = 'Confirm password must match password.';
  }

  if (!values.securityQuestion.trim()) {
    errors.securityQuestion = 'Security question is required.';
  }

  if (!values.securityAnswer.trim()) {
    errors.securityAnswer = 'Security answer is required.';
  }

  if (!values.name.trim()) {
    errors.name = 'Name is required.';
  }

  if (!['Male', 'Female', 'Transgender'].includes(values.gender)) {
    errors.gender = 'Select a valid gender.';
  }

  if (!values.dateOfBirth) {
    errors.dateOfBirth = 'Date of birth is required.';
  }

  if (!values.occupation.trim()) {
    errors.occupation = 'Occupation is required.';
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!/^\d{10,15}$/.test(values.mobile)) {
    errors.mobile = 'Mobile must contain 10 to 15 digits.';
  }

  if (!values.nationality.trim()) {
    errors.nationality = 'Nationality is required.';
  }

  return errors;
}

export default function SignupPage() {
  const [values, setValues] = useState(DEFAULT_VALUES);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { setUser } = useAuth();
  const navigate = useNavigate();

  function onChange(event) {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setFormError('');

    const nextErrors = validate(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await signup(values);
      setUser(result.user);
      navigate('/signup/success');
    } catch (error) {
      setFormError(error.message || 'Unable to complete signup.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.panel} aria-labelledby="signup-title">
        <h1 id="signup-title" className={styles.title}>
          Form C User Registration
        </h1>
        <p>Register your account with mandatory profile and recovery details.</p>

        {formError ? (
          <p className={styles.formError} role="alert" aria-live="polite">
            {formError}
          </p>
        ) : null}

        <form onSubmit={onSubmit} noValidate>
          <div className={styles.grid}>
            <Field label="User ID" name="userId" value={values.userId} onChange={onChange} error={errors.userId} />
            <Field
              label="Email"
              name="email"
              type="email"
              value={values.email}
              onChange={onChange}
              error={errors.email}
            />

            <Field
              label="Password"
              name="password"
              type="password"
              value={values.password}
              onChange={onChange}
              error={errors.password}
            />
            <Field
              label="Confirm Password"
              name="confirmPassword"
              type="password"
              value={values.confirmPassword}
              onChange={onChange}
              error={errors.confirmPassword}
            />

            <Field
              label="Security Question"
              name="securityQuestion"
              value={values.securityQuestion}
              onChange={onChange}
              error={errors.securityQuestion}
              className={styles.full}
            />
            <Field
              label="Security Answer"
              name="securityAnswer"
              value={values.securityAnswer}
              onChange={onChange}
              error={errors.securityAnswer}
              className={styles.full}
            />

            <Field label="Name" name="name" value={values.name} onChange={onChange} error={errors.name} />
            <SelectField
              label="Gender"
              name="gender"
              value={values.gender}
              onChange={onChange}
              error={errors.gender}
              options={[
                { label: 'Select', value: '' },
                { label: 'Male', value: 'Male' },
                { label: 'Female', value: 'Female' },
                { label: 'Transgender', value: 'Transgender' }
              ]}
            />

            <Field
              label="Date of Birth"
              name="dateOfBirth"
              type="date"
              value={values.dateOfBirth}
              onChange={onChange}
              error={errors.dateOfBirth}
            />
            <Field
              label="Occupation"
              name="occupation"
              value={values.occupation}
              onChange={onChange}
              error={errors.occupation}
            />

            <Field label="Mobile" name="mobile" value={values.mobile} onChange={onChange} error={errors.mobile} />
            <Field
              label="Nationality"
              name="nationality"
              value={values.nationality}
              onChange={onChange}
              error={errors.nationality}
            />
          </div>

          <div className={styles.actions}>
            <button className={styles.button} type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Create Account'}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

function Field({ label, name, type = 'text', value, onChange, error, className = '' }) {
  const id = `field-${name}`;
  const errorId = `${id}-error`;

  return (
    <div className={`${styles.field} ${className}`}>
      <label htmlFor={id}>{label}</label>
      <input
        className={styles.input}
        id={id}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
      />
      {error ? (
        <span id={errorId} className={styles.error} role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}

function SelectField({ label, name, value, onChange, error, options }) {
  const id = `field-${name}`;
  const errorId = `${id}-error`;

  return (
    <div className={styles.field}>
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        name={name}
        className={styles.select}
        value={value}
        onChange={onChange}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
      >
        {options.map((option) => (
          <option key={option.value || 'empty'} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? (
        <span id={errorId} className={styles.error} role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}
