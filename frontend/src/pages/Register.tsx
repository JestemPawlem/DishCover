import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registerUser } from '../api/auth';
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
    Text,
    Anchor
} from '@mantine/core'


export const Register = () => {
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
            await registerUser({ email, password });
            navigate('/login');
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
                Sign Up
            </Title>

            <form onSubmit={handleSubmit}>
                <Stack gap='md'>
                {error && (
                    <Alert color='red' radius='md' title='Registration Error'>
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
                    description='Min. 8 characters, at least one letter and number'
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
                    Sign Up
                </Button>
                </Stack>
            </form>

            <Text c='dimmed' size='sm' ta='center' mt='xl'>
                Already have an account?{' '}
                <Anchor component={Link} to='/login' size='sm' fw={600} c='teal.9'>
                Sign in
                </Anchor>
            </Text>
            </Paper>
        </Container>
        </Box>
    );
};