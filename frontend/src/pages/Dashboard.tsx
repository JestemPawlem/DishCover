import { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  Button,
  Group,
  Tabs
} from '@mantine/core';
import { IconSparkles, IconStar } from '@tabler/icons-react';

import type { UserResponse } from '../types/auth';
import { RecommendedRecipes } from '../components/RecommendedRecipes';
import { PopularRecipes } from '../components/PopularRecipes';

interface OutletContextType {
  user: UserResponse | null;
  isLoggedIn: boolean;
}

export const Dashboard = () => {
  const { isLoggedIn } = useOutletContext<OutletContextType>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<string | null>(isLoggedIn ? 'recommended' : 'popular');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTabChange = (val: string | null) => {
    if (val === 'recommended' && !isLoggedIn) {
      navigate('/login');
      return;
    }
    setActiveTab(val);
  };

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <Container size='lg'>
      <Paper shadow='2xl' p={36} radius='xl' bg='white'>
        <Group justify='space-between' align='center' mb='lg'>
          <div>
            <Title order={2} fw={800} c='teal.9'>
              {activeTab === 'recommended' ? 'Recommended' : 'Popular'}
            </Title>
            <Text c='dimmed' size='sm'>
              {activeTab === 'recommended'
                ? 'Personalized recipe suggestions based on your taste'
                : 'Most liked recipes across the platform'}
            </Text>
          </div>

          <Group gap='sm'>
            <Tabs value={activeTab} onChange={handleTabChange} variant='pills' color='teal'>
              <Tabs.List>
                <Tabs.Tab value='recommended' leftSection={<IconSparkles size={14} stroke={1.7} />}>
                  Recommended
                </Tabs.Tab>
                <Tabs.Tab value='popular' leftSection={<IconStar size={14} stroke={1.7} />}>
                  Popular
                </Tabs.Tab>
              </Tabs.List>
            </Tabs>

            <Button
              variant='subtle'
              color='teal'
              radius='md'
              size='xs'
              onClick={handleRefresh}
            >
              Refresh
            </Button>
          </Group>
        </Group>

        {activeTab === 'recommended' ? (
          <RecommendedRecipes isLoggedIn={isLoggedIn} refreshKey={refreshKey} />
        ) : (
          <PopularRecipes isLoggedIn={isLoggedIn} refreshKey={refreshKey} />
        )}
      </Paper>
    </Container>
  );
};