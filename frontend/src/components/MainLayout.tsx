import { useEffect, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Box } from '@mantine/core';
import { getCurrentUser } from '../api/auth';
import type { UserResponse } from '../types/auth';
import { AppHeader } from './AppHeader';


export const MainLayout = () => {
    const [user, setUser] = useState<UserResponse | null>(null);
    const navigate = useNavigate();


    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            getCurrentUser()
                .then(setUser)
                .catch(() => {
                    localStorage.removeItem('token');
                    setUser(null);
                });
        }
    }, []);


    const handleLogout = () => {
        localStorage.removeItem('token');
        setUser(null);
        navigate('/login');
    };


    return (
        <Box bg='teal.5' mih='100vh'>
            <AppHeader user={user} onLogout={handleLogout} />
            <Box py='xl' px='md'>
                <Outlet context={{ user, isLoggedIn: !!user }} />
            </Box>
        </Box>
    );
};