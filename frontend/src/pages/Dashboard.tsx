import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../api/auth';
import { type UserResponse } from '../types/user';

import {
  Box,
  Container,
  Paper,
  Title,
  Text,
  Button,
  Stack,
  Group,
  Divider,
  Badge,
  Card,
} from '@mantine/core';


export const Dashboard = () => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getCurrentUser()
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem('token');
        navigate('/login');
      });
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (!user) {
    return <p style={{ textAlign: 'center', marginTop: '50px' }}>Ładowanie profilu...</p>;
  }

  return (
    <Box bg='teal.5' mih='100vh' py='xl' px='md'>
      <Container size={640}>
        <Paper shadow='2xl' p={36} radius='xl' bg='white'>
          <Group justify='space-between' align='center' mb='lg'>
            <div>
              <Title order={2} fw={800} c='teal.9'>
                Panel użytkownika
              </Title>
              <Text c='dimmed' size='sm'>
                Zalogowano pomyślnie
              </Text>
            </div>
            <Button
              variant='light'
              color='red'
              radius='md'
              onClick={handleLogout}
            >
              Wyloguj
            </Button>
          </Group>

          <Divider my='md' />

          <Stack gap='xs' mb='xl'>
            <Group justify='space-between'>
              <Text fw={600} size='sm'>Email:</Text>
              <Text size='sm'>{user.email}</Text>
            </Group>

            <Group justify='space-between'>
              <Text fw={600} size='sm'>ID użytkownika:</Text>
              <Badge color='gray' variant='light'>{user.id}</Badge>
            </Group>

            <Group justify='space-between'>
              <Text fw={600} size='sm'>Konto utworzone:</Text>
              <Text size='sm'>{new Date(user.created_at).toLocaleDateString()}</Text>
            </Group>
          </Stack>

          <Card withBorder radius='lg' p='lg' bg='gray.0'>
            <Title order={4} c='teal.8' mb='xs'>
              Rekomendacje przepisów
            </Title>
            <Text size='sm' c='dimmed'>
              Tutaj podepniemy model PyTorch i wyświetlanie wyników predykcji.
            </Text>
          </Card>
        </Paper>
      </Container>
    </Box>
  );
};