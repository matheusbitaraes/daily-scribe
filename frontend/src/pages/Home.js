import SubscriptionForm from '../components/SubscriptionForm';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';



const Home = () => {

  return (
    <Box>
      <Container maxWidth="md" sx={{ textAlign: 'center', marginTop: '2rem', marginBottom: '2rem' }}>
        <Typography variant="h1" component="h1" sx={{ fontSize: '3.5rem', fontWeight: '600' }}>
          Daily Scribe
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Your curated news articles from trusted sources
        </Typography>
      </Container>
      <SubscriptionForm />
    </Box>
  );
};

export default Home;
