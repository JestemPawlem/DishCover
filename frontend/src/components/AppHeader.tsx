import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    Box,
    Container,
    Group,
    TextInput,
    Button,
    Menu,
    Avatar,
    Text
} from '@mantine/core';
import type { UserResponse } from '../types/auth';


interface Props {
    user: UserResponse | null;
    onLogout: () => void;
}


export const AppHeader = ({ user, onLogout }: Props) => {
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();


    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const trimmed = searchQuery.trim();
        if (trimmed) {
            navigate(`/search?q=${encodeURIComponent(trimmed)}`);
        }
    };


    return (
        <Box component='header' bg='white' style={{ borderBottom: '1px solid #e9ecef' }} py='sm'>
            <Container size='lg'>
                <Group justify='space-between' align='center'>
                    <Text
                        component={Link}
                        to='/'
                        fw={900}
                        size='xl'
                        c='teal.8'
                        style={{ textDecoration: 'none' }}
                    >
                        TasteMatch
                    </Text>

                    <form onSubmit={handleSearch} style={{ flex: 1, maxWidth: 440 }}>
                        <TextInput
                            placeholder='Search recipes...'
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.currentTarget.value)}
                            radius='xl'
                            size='sm'
                        />
                    </form>

                    <Group gap='sm'>
                        {user ? (
                            <>
                                <Button
                                    component={Link}
                                    to='/favorites'
                                    variant='subtle'
                                    color='teal'
                                    size='sm'
                                >
                                    Saved Recipes
                                </Button>

                                <Menu shadow='md' width={200} position='bottom-end'>
                                    <Menu.Target>
                                        <Avatar color='teal' radius='xl' style={{ cursor: 'pointer' }}>
                                            {user.email[0].toUpperCase()}
                                        </Avatar>
                                    </Menu.Target>

                                    <Menu.Dropdown>
                                        <Menu.Label>Signed in as</Menu.Label>
                                        <Menu.Item disabled>
                                            <Text size='xs' truncate>{user.email}</Text>
                                        </Menu.Item>
                                        <Menu.Divider />
                                        <Menu.Item color='red' onClick={onLogout}>
                                            Sign out
                                        </Menu.Item>
                                    </Menu.Dropdown>
                                </Menu>
                            </>
                        ) : (
                            <Group gap='xs'>
                                <Button component={Link} to='/login' variant='subtle' color='teal' size='sm'>
                                    Sign in
                                </Button>
                                <Button component={Link} to='/register' variant='filled' color='teal' size='sm'>
                                    Sign up
                                </Button>
                            </Group>
                        )}
                    </Group>
                </Group>
            </Container>
        </Box>
    );
};