import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext.jsx';
import SignupPage from './SignupPage.jsx';
import SignupSuccessPage from '../../pages/SignupSuccessPage.jsx';
import { signup } from '../../services/authApi.js';

jest.mock('../../services/authApi.js', () => ({
  signup: jest.fn()
}));

function renderWithRouter() {
  return render(
    <MemoryRouter initialEntries={['/signup']}>
      <AuthProvider>
        <Routes>
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/signup/success" element={<SignupSuccessPage />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

async function fillValidForm(user) {
  await user.type(screen.getByLabelText(/User ID/i), 'User123');
  await user.type(screen.getByLabelText(/^Email$/i), 'john@example.com');
  await user.type(screen.getByLabelText(/^Password$/i), 'Welcome@123');
  await user.type(screen.getByLabelText(/Confirm Password/i), 'Welcome@123');
  await user.type(screen.getByLabelText(/Security Question/i), 'Favorite author?');
  await user.type(screen.getByLabelText(/Security Answer/i), 'Tagore');
  await user.type(screen.getByLabelText(/^Name$/i), 'John Doe');
  await user.selectOptions(screen.getByLabelText(/Gender/i), 'Male');
  await user.type(screen.getByLabelText(/Date of Birth/i), '1990-01-01');
  await user.type(screen.getByLabelText(/Occupation/i), 'Hotel Owner');
  await user.type(screen.getByLabelText(/Mobile/i), '9876543210');
}

describe('SignupPage', () => {
  beforeEach(() => {
    signup.mockReset();
  });

  it('shows field validation errors on invalid submit', async () => {
    const user = userEvent.setup();
    renderWithRouter();

    await user.click(screen.getByRole('button', { name: /Create Account/i }));

    expect(screen.getByText(/User ID must include/i)).toBeInTheDocument();
    expect(screen.getByText(/Password must include/i)).toBeInTheDocument();
    expect(screen.getByText(/Security question is required/i)).toBeInTheDocument();
  });

  it('submits valid form and navigates to success page', async () => {
    const user = userEvent.setup();
    signup.mockResolvedValue({
      user: {
        userId: 'User123'
      }
    });
    renderWithRouter();

    await fillValidForm(user);
    await user.click(screen.getByRole('button', { name: /Create Account/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Registration Completed/i })).toBeInTheDocument();
    });
    expect(signup).toHaveBeenCalledTimes(1);
  });

  it('renders form-level error when signup api fails', async () => {
    const user = userEvent.setup();
    signup.mockRejectedValue(new Error('User ID already exists'));
    renderWithRouter();

    await fillValidForm(user);
    await user.click(screen.getByRole('button', { name: /Create Account/i }));

    await waitFor(() => {
      expect(screen.getByText(/User ID already exists/i)).toBeInTheDocument();
    });
  });
});
