import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { loginUser, registerUser, saveToken } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginUser(loginData);
      saveToken(response.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível entrar.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await registerUser(registerData);
      const response = await loginUser({
        email: registerData.email,
        password: registerData.password,
      });
      saveToken(response.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível criar a conta.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-grid">
      <div className="card auth-card">
        <h2>Entrar</h2>
        <form className="stacked-form" onSubmit={handleLogin}>
          <label>
            E-mail
            <input
              type="email"
              placeholder="seu@email.com"
              required
              value={loginData.email}
              onChange={(event) => setLoginData((current) => ({ ...current, email: event.target.value }))}
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              placeholder="••••••••"
              required
              value={loginData.password}
              onChange={(event) => setLoginData((current) => ({ ...current, password: event.target.value }))}
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Entrando...' : 'Acessar painel'}
          </button>
        </form>
      </div>

      <div className="card auth-card">
        <h2>Criar conta</h2>
        <form className="stacked-form" onSubmit={handleRegister}>
          <label>
            Nome
            <input
              type="text"
              placeholder="Seu nome"
              required
              value={registerData.name}
              onChange={(event) => setRegisterData((current) => ({ ...current, name: event.target.value }))}
            />
          </label>
          <label>
            E-mail
            <input
              type="email"
              placeholder="seu@email.com"
              required
              value={registerData.email}
              onChange={(event) => setRegisterData((current) => ({ ...current, email: event.target.value }))}
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              placeholder="Crie uma senha"
              minLength={8}
              required
              value={registerData.password}
              onChange={(event) => setRegisterData((current) => ({ ...current, password: event.target.value }))}
            />
          </label>
          <button type="submit" className="secondary" disabled={loading}>
            {loading ? 'Registrando...' : 'Registrar'}
          </button>
        </form>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
    </section>
  );
}
