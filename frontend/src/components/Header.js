import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';

const Header = () => {

  return (
    <Container maxWidth="lg" sx={{ textAlign: 'center', marginTop: '2rem', marginBottom: '2rem' }}>
      <Typography variant="h4" component="h4" sx={{ fontSize: '2rem', fontWeight: '600' }}>
        Daily Scribe
      </Typography>
      <Divider sx={{ marginTop: '0.5rem', marginBottom: '0.5rem' }} />

    </Container>
  );
};

export default Header;
