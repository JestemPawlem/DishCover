import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../api/auth';
import axios from 'axios';

import {
    Box,
    Container,
    Paper,
    Title,
    TextInput,
    PasswordInput,
    Button,
    Alert,
    Stack,
} from '@mantine/core';


export const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const data = await loginUser({ email, password });
            localStorage.setItem('token', data.access_token);
            navigate('/dashboard', { replace: true });
        } catch (err: unknown) {
            if (axios.isAxiosError(err) && err.response) {
                const detail = err.response.data?.detail;

                if (typeof detail === 'string') {
                    setError(detail);
                } else if (Array.isArray(detail)) {
                    const messages = detail.map((d: { msg?: string }) => d.msg || 'Validation error');
                    setError(messages.join(', '));
                } else {
                    setError('Błąd walidacji formularza');
                }
            } else {
                setError('Wystąpił nieoczekiwany błąd');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box bg='teal.7' mih='100vh' style={{ display: 'grid', placeItems: 'center' }} p='md'>
        <Container size={420} w='100%'>
            <Paper
            shadow='2xl'
            p={36}
            radius='xl'
            bg='gray.3'
            >
            <Title ta='center' order={2} fw={800} mb='xl' c='teal.9'>
                Sign In
            </Title>

            <form onSubmit={handleSubmit}>
                <Stack gap='md'>
                {error && (
                    <Alert color='red' radius='md' title='Authentication Error'>
                    {error}
                    </Alert>
                )}

                <TextInput
                    label='Email'
                    placeholder='name@example.com'
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <PasswordInput
                    label='Password'
                    placeholder='••••••••'
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />

                <Button
                    type='submit'
                    fullWidth
                    color='teal.9'
                    size='md'
                    radius='md'
                    loading={loading}
                    mt='sm'
                >
                    Sign In
                </Button>
                </Stack>
            </form>
            </Paper>
        </Container>
        </Box>
    );
};